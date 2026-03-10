"""
LLM call pipeline — generates files and diagnoses/fixes errors.
"""
import json
import re
from backend.llm.client import chat_completion
from backend.llm.prompts import BUILD_PROMPT, FIX_PROMPT, ALTERNATE_FIX_PROMPT, DIAGNOSE_PROMPT
from backend.utils.logger import log_action, log_error


async def execute(
    action: dict,
    file_map: dict,
    task_description: str,
    full_file_dump: str,
    base_url: str,
    model: str,
) -> dict:
    """
    Execute a single build action by calling the LLM.

    Args:
        action: {"action": "create|edit|delete", "file": "path", "instruction": "what to do"}
        file_map: The current project file map from the auditor
        task_description: The original user task description
        full_file_dump: Complete project source dump
        base_url: LM Studio API URL
        model: Model ID

    Returns:
        {"file": str, "content": str, "action": str}
    """
    instruction = action.get("instruction", "")
    file_path = action.get("file", "")
    action_type = action.get("action", "create")

    prompt = BUILD_PROMPT.format(
        full_file_dump=full_file_dump[:80000],  # Truncate to stay within context
        task_description=task_description,
        action_instruction=f"Action: {action_type} file '{file_path}'\nInstruction: {instruction}",
    )

    log_action("builder", f"Generating: {action_type} {file_path}")

    messages = [
        {"role": "system", "content": "You are Forge, an autonomous build agent. Return ONLY raw file content. No explanations, no markdown fences."},
        {"role": "user", "content": prompt},
    ]

    content = await chat_completion(base_url, model, messages, max_tokens=4096)

    # Strip markdown fences if the LLM wrapped them anyway
    content = _strip_fences(content)

    return {"file": file_path, "content": content, "action": action_type}


async def diagnose_and_fix(
    error_result: dict,
    file_map: dict,
    relevant_files: str,
    base_url: str,
    model: str,
) -> list[dict]:
    """
    Diagnose a build/test error and return patches.

    Returns:
        List of patch dicts: [{"file": ..., "patch_type": ..., "target": ..., "replacement": ...}]
    """
    file_map_summary = json.dumps(
        {k: {"purpose": v["purpose"], "language": v["language"]} for k, v in file_map.items()},
        indent=2,
    )

    prompt = FIX_PROMPT.format(
        error_output=f"Exit code: {error_result.get('exit_code')}\n"
                     f"Error type: {error_result.get('error_type', 'unknown')}\n"
                     f"Location: {error_result.get('error_location', 'unknown')}\n"
                     f"STDOUT:\n{error_result.get('stdout', '')[:2000]}\n"
                     f"STDERR:\n{error_result.get('stderr', '')[:2000]}",
        relevant_file_contents=relevant_files[:60000],
    )

    messages = [
        {"role": "system", "content": "You are Forge. Return JSON patches only. No explanation."},
        {"role": "user", "content": prompt},
    ]

    log_action("builder", "Diagnosing error and generating fix")
    response = await chat_completion(base_url, model, messages, max_tokens=4096)

    return _parse_patches(response)


async def alternate_fix(
    error_result: dict,
    file_map: dict,
    relevant_files: str,
    previous_fixes: str,
    occurrences: int,
    base_url: str,
    model: str,
) -> list[dict]:
    """
    Generate an alternative fix when the same error keeps occurring.
    """
    prompt = ALTERNATE_FIX_PROMPT.format(
        error_output=f"STDERR:\n{error_result.get('stderr', '')[:2000]}",
        relevant_file_contents=relevant_files[:40000],
        previous_fixes=previous_fixes[:4000],
        occurrences=occurrences,
    )

    messages = [
        {"role": "system", "content": "You are Forge. Try a completely different fix approach. Return JSON patches only."},
        {"role": "user", "content": prompt},
    ]

    log_action("builder", f"Generating alternate fix (error seen {occurrences} times)")
    response = await chat_completion(base_url, model, messages, max_tokens=4096)

    return _parse_patches(response)


def _strip_fences(text: str) -> str:
    """Remove markdown code fences from LLM output."""
    text = text.strip()
    # Remove opening fence with optional language tag
    if text.startswith("```"):
        first_newline = text.index("\n") if "\n" in text else len(text)
        text = text[first_newline + 1:]
    # Remove closing fence
    if text.rstrip().endswith("```"):
        text = text.rstrip()[:-3].rstrip()
    return text


def _parse_patches(response: str) -> list[dict]:
    """Parse LLM response into patch dicts."""
    response = _strip_fences(response)

    try:
        parsed = json.loads(response)
        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    # Try to find JSON in the response
    json_match = re.search(r'[\[{].*[\]}]', response, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, dict):
                return [parsed]
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    log_error("builder", "Could not parse LLM response as JSON patches")
    return []
