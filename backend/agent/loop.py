"""
The core build loop — the heart of Forge.
4 phases: Audit → Build → Run & Fix → Test
"""
import hashlib
import json
import os
from datetime import datetime, timezone

from backend.agent import auditor, builder, patcher, runner, tester
from backend.llm.client import chat_completion
from backend.llm.prompts import AUDIT_PROMPT
from backend.utils.logger import log_action, log_error, log


async def run_build(
    project_path: str,
    task_description: str,
    config: dict,
    broadcast=None,
):
    """
    Execute the full 4-phase build loop.

    Args:
        project_path: Absolute path to the project directory.
        task_description: Plain-English description of what to build.
        config: Forge config dict (from forge.config.json).
        broadcast: Async callable(event_dict) to emit WebSocket events.

    Returns:
        {"success": bool, "detail": str, "iterations": int}
    """
    base_url = config["lm_studio_url"]
    max_iters = config.get("max_fix_iterations", 10)
    circ_threshold = config.get("circular_error_threshold", 3)
    project_name = os.path.basename(project_path)

    # Resolve model — use override if set, otherwise auto-detect was done at startup
    model = config.get("_active_model")
    if not model:
        from backend.llm.vram import select_model
        model_info = select_model(base_url)
        model = model_info.get("model")
        if not model:
            return {"success": False, "detail": "No model available in LM Studio", "iterations": 0}

    async def emit(event: dict):
        event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        log_action("event", event.get("event", "UNKNOWN"), event)
        if broadcast:
            await broadcast(event)

    await emit({"event": "BUILD_STARTED", "project": project_name})

    # ── PHASE 1 — AUDIT ──────────────────────────────────────────────
    log_action("loop", "Phase 1 — AUDIT", {"project": project_name})

    scan_result = auditor.scan(project_path)
    file_map = scan_result["file_map"]
    full_dump = auditor.get_full_dump(project_path)

    # Ask LLM for build plan
    audit_prompt = AUDIT_PROMPT.format(
        full_file_dump=full_dump[:80000],
        task_description=task_description,
    )

    messages = [
        {"role": "system", "content": "You are Forge, an autonomous build agent. Return JSON only."},
        {"role": "user", "content": audit_prompt},
    ]

    plan_raw = await chat_completion(base_url, model, messages, max_tokens=4096)

    # Parse build plan
    build_plan = []
    try:
        plan_json = json.loads(_strip_fences(plan_raw))
        build_plan = plan_json.get("build_plan", [])
        detected_issues = plan_json.get("detected_issues", [])
        log_action("loop", f"Build plan: {len(build_plan)} actions, {len(detected_issues)} issues detected")
    except json.JSONDecodeError:
        log_error("loop", "Failed to parse audit plan — using empty plan")
        # If the project is empty, generate a single "create all files" action
        if not file_map:
            build_plan = [{"action": "create", "file": "main.py", "instruction": task_description}]

    # ── PHASE 2 — BUILD ──────────────────────────────────────────────
    log_action("loop", "Phase 2 — BUILD", {"actions": len(build_plan)})

    for i, action in enumerate(build_plan):
        # Normalize file path — strip leading slashes so files stay inside project dir
        if "file" in action:
            action["file"] = action["file"].lstrip("/").lstrip("\\")

        log_action("loop", f"Build action {i+1}/{len(build_plan)}: {action.get('action')} {action.get('file')}")

        if action.get("action") == "delete":
            target = os.path.join(project_path, action.get("file", ""))
            if os.path.exists(target):
                os.remove(target)
                await emit({"event": "FILE_CHANGED", "file": action["file"], "diff": "deleted"})
            continue

        result = await builder.execute(
            action=action,
            file_map=file_map,
            task_description=task_description,
            full_file_dump=full_dump[:80000],
            base_url=base_url,
            model=model,
        )

        # Normalize output file path
        result["file"] = result["file"].lstrip("/").lstrip("\\")

        # Write file
        file_path = os.path.join(project_path, result["file"])
        os.makedirs(os.path.dirname(file_path) or project_path, exist_ok=True)

        before = ""
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    before = f.read()
            except Exception:
                pass

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(result["content"])

        await emit({
            "event": "FILE_CHANGED",
            "file": result["file"],
            "diff": f"before: {len(before)} chars → after: {len(result['content'])} chars",
        })

    # Install dependencies after generating files
    dep_result = runner.install_dependencies(project_path)
    if not dep_result["success"]:
        log_error("loop", "Dependency installation failed", dep_result)

    # Re-scan after build
    scan_result = auditor.scan(project_path)
    file_map = scan_result["file_map"]

    # ── PHASE 3 — RUN & FIX LOOP ─────────────────────────────────────
    log_action("loop", "Phase 3 — RUN & FIX LOOP")

    iteration = 0
    error_history: dict[str, int] = {}
    fix_log: list[str] = []

    while iteration < max_iters:
        run_result = runner.run(project_path)

        if run_result["success"]:
            log_action("loop", f"Run succeeded on iteration {iteration}")
            break

        # Build error signature
        sig_input = f"{run_result.get('error_type', '')}:{run_result.get('error_location', '')}"
        error_sig = hashlib.sha256(sig_input.encode()).hexdigest()[:16]
        error_history[error_sig] = error_history.get(error_sig, 0) + 1

        await emit({
            "event": "BUILD_ERROR",
            "error": run_result.get("stderr", "")[:500],
            "iteration": iteration + 1,
        })

        # Gather relevant files for the fix context
        relevant = auditor.get_full_dump(project_path)

        if error_history[error_sig] >= circ_threshold:
            # Circular error — try alternate strategy
            log_action("loop", f"Circular error detected (seen {error_history[error_sig]} times). Trying alternate fix.")
            patches = await builder.alternate_fix(
                error_result=run_result,
                file_map=file_map,
                relevant_files=relevant,
                previous_fixes="\n".join(fix_log[-5:]),
                occurrences=error_history[error_sig],
                base_url=base_url,
                model=model,
            )
            error_history = {}  # Reset after strategy change
        else:
            patches = await builder.diagnose_and_fix(
                error_result=run_result,
                file_map=file_map,
                relevant_files=relevant,
                base_url=base_url,
                model=model,
            )

        # Apply patches
        for patch in patches:
            result = patcher.apply(project_path, patch)
            fix_log.append(f"iter={iteration+1} file={patch.get('file')} result={result['detail']}")

            await emit({
                "event": "FIX_APPLIED",
                "file": patch.get("file", ""),
                "summary": result["detail"],
            })

        iteration += 1

    if iteration >= max_iters and not run_result.get("success"):
        await emit({
            "event": "BUILD_FAILED",
            "reason": f"Max iterations ({max_iters}) reached. Last error: {run_result.get('stderr', '')[:300]}",
            "iterations": iteration,
        })
        return {"success": False, "detail": "Max fix iterations reached", "iterations": iteration}

    # ── PHASE 4 — TEST ────────────────────────────────────────────────
    log_action("loop", "Phase 4 — TEST")

    detection = tester.detect(project_path)
    if detection is None:
        log_action("loop", "No tests found — skipping Phase 4")
        await emit({"event": "BUILD_COMPLETE", "project": project_name, "duration_seconds": 0})
        return {"success": True, "detail": "Build complete (no tests)", "iterations": iteration}

    await emit({"event": "TESTS_RUNNING", "framework": detection["framework"]})
    test_result = tester.run(project_path)

    # Feed test failures back into fix loop
    remaining_iters = max_iters - iteration
    test_iter = 0
    while not test_result["success"] and test_iter < remaining_iters:
        for failure in test_result.get("failures", []):
            await emit({
                "event": "TEST_FAILED",
                "test": failure.get("test", "unknown"),
                "error": failure.get("error", "")[:500],
            })

        relevant = auditor.get_full_dump(project_path)
        # Convert test result to error format for the builder
        error_for_builder = {
            "exit_code": test_result.get("exit_code", 1),
            "stdout": test_result.get("stdout", ""),
            "stderr": test_result.get("stderr", ""),
            "error_type": "test_failure",
            "error_location": None,
        }
        patches = await builder.diagnose_and_fix(
            error_result=error_for_builder,
            file_map=file_map,
            relevant_files=relevant,
            base_url=base_url,
            model=model,
        )

        for patch in patches:
            result = patcher.apply(project_path, patch)
            await emit({
                "event": "FIX_APPLIED",
                "file": patch.get("file", ""),
                "summary": result["detail"],
            })

        test_result = tester.run(project_path)
        test_iter += 1
        iteration += 1

    if not test_result["success"]:
        await emit({
            "event": "BUILD_FAILED",
            "reason": f"Tests still failing: {test_result.get('summary', '')}",
            "iterations": iteration,
        })
        return {"success": False, "detail": "Tests failed", "iterations": iteration}

    await emit({"event": "BUILD_COMPLETE", "project": project_name, "duration_seconds": 0})
    return {"success": True, "detail": "Build complete — all tests passed", "iterations": iteration}


def _strip_fences(text: str) -> str:
    """Remove markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        nl = text.index("\n") if "\n" in text else len(text)
        text = text[nl + 1:]
    if text.rstrip().endswith("```"):
        text = text.rstrip()[:-3].rstrip()
    return text
