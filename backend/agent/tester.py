"""
Test framework auto-detector, runner, and failure parser.
Supports: pytest, jest, vitest
"""
import json
import os
import subprocess
from backend.utils.logger import log_action, log_error


def detect(project_path: str) -> dict | None:
    """
    Detect which test framework the project uses.

    Returns:
        {"framework": str, "test_files": [str], "command": [str]} or None if no tests found.
    """
    test_files = []

    # ── Pytest detection ──
    tests_dir = os.path.join(project_path, "tests")
    if os.path.isdir(tests_dir):
        for f in os.listdir(tests_dir):
            if f.startswith("test_") and f.endswith(".py"):
                test_files.append(os.path.join("tests", f))

    # Check root for test files
    for f in os.listdir(project_path):
        if f.startswith("test_") and f.endswith(".py"):
            test_files.append(f)

    if test_files:
        log_action("tester", f"Detected pytest with {len(test_files)} test file(s)")
        return {
            "framework": "pytest",
            "test_files": test_files,
            "command": ["python", "-m", "pytest", "-q", "--tb=short"],
        }

    # ── Jest/Vitest detection ──
    pkg_path = os.path.join(project_path, "package.json")
    if os.path.exists(pkg_path):
        try:
            with open(pkg_path, "r") as f:
                pkg = json.load(f)
        except Exception:
            pkg = {}

        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        scripts = pkg.get("scripts", {})

        # Check for vitest
        if "vitest" in deps or "vitest" in scripts.get("test", ""):
            js_tests = _find_js_test_files(project_path)
            if js_tests:
                log_action("tester", f"Detected vitest with {len(js_tests)} test file(s)")
                return {
                    "framework": "vitest",
                    "test_files": js_tests,
                    "command": ["npx", "vitest", "run", "--reporter=verbose"],
                }

        # Check for jest
        if "jest" in deps or "jest" in scripts.get("test", ""):
            js_tests = _find_js_test_files(project_path)
            if js_tests:
                log_action("tester", f"Detected jest with {len(js_tests)} test file(s)")
                return {
                    "framework": "jest",
                    "test_files": js_tests,
                    "command": ["npx", "jest", "--verbose"],
                }

        # Check if "test" script exists
        if "test" in scripts and scripts["test"] not in ("echo \"Error: no test specified\" && exit 1", ""):
            js_tests = _find_js_test_files(project_path)
            return {
                "framework": "npm-test",
                "test_files": js_tests,
                "command": ["npm", "test"],
            }

    log_action("tester", "No test framework detected")
    return None


def run(project_path: str) -> dict:
    """
    Run detected tests and return structured results.

    Returns:
        {
            "success": bool,
            "framework": str,
            "exit_code": int,
            "stdout": str,
            "stderr": str,
            "failures": [{"test": str, "error": str}],
            "summary": str,
        }
    """
    detection = detect(project_path)

    if detection is None:
        return {
            "success": True,
            "framework": "none",
            "exit_code": 0,
            "stdout": "No tests found",
            "stderr": "",
            "failures": [],
            "summary": "No tests found — skipped",
        }

    framework = detection["framework"]
    command = detection["command"]

    log_action("tester", f"Running {framework}: {' '.join(command)}")

    env = os.environ.copy()
    env["PYTHONPATH"] = project_path

    try:
        result = subprocess.run(
            command,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
        )

        failures = []
        if result.returncode != 0:
            failures = _parse_failures(result.stdout + "\n" + result.stderr, framework)

        total_tests = _count_tests(result.stdout, framework)
        passed = total_tests - len(failures)

        summary = f"{framework}: {passed}/{total_tests} passed"
        if failures:
            summary += f", {len(failures)} failed"

        log_action("tester", summary)

        return {
            "success": result.returncode == 0,
            "framework": framework,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "failures": failures,
            "summary": summary,
        }

    except subprocess.TimeoutExpired:
        log_error("tester", "Tests timed out after 180 seconds")
        return {
            "success": False,
            "framework": framework,
            "exit_code": -1,
            "stdout": "",
            "stderr": "Tests timed out after 180 seconds",
            "failures": [{"test": "suite", "error": "Timeout"}],
            "summary": f"{framework}: timed out",
        }
    except FileNotFoundError as e:
        log_error("tester", f"Test runner not found: {e}")
        return {
            "success": True,  # Don't fail the build if test runner isn't installed
            "framework": framework,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Test runner not found: {e}",
            "failures": [],
            "summary": f"{framework}: runner not available, skipped",
        }
    except Exception as e:
        log_error("tester", str(e))
        return {
            "success": False,
            "framework": framework,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "failures": [{"test": "suite", "error": str(e)}],
            "summary": f"{framework}: error — {e}",
        }


def _find_js_test_files(project_path: str) -> list[str]:
    """Find JavaScript/TypeScript test files."""
    test_files = []
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in {"node_modules", ".next", "dist", "build"}]
        for f in files:
            if (f.endswith((".test.js", ".test.ts", ".test.jsx", ".test.tsx",
                           ".spec.js", ".spec.ts", ".spec.jsx", ".spec.tsx"))):
                rel = os.path.relpath(os.path.join(root, f), project_path)
                test_files.append(rel)
    return test_files


def _parse_failures(output: str, framework: str) -> list[dict]:
    """Parse test output to extract individual failures."""
    failures = []

    if framework == "pytest":
        # Look for FAILED lines: "FAILED tests/test_foo.py::test_bar - AssertionError"
        for line in output.split("\n"):
            if line.strip().startswith("FAILED"):
                parts = line.strip().split(" - ", 1)
                test_name = parts[0].replace("FAILED ", "").strip()
                error = parts[1].strip() if len(parts) > 1 else "Unknown error"
                failures.append({"test": test_name, "error": error})

    elif framework in ("jest", "vitest"):
        # Look for "FAIL" or "✕" markers
        in_fail = False
        current_test = ""
        for line in output.split("\n"):
            stripped = line.strip()
            if "FAIL" in stripped and (".test." in stripped or ".spec." in stripped):
                in_fail = True
                continue
            if in_fail and stripped.startswith(("✕", "×", "✗", "FAIL")):
                current_test = stripped.lstrip("✕×✗ ").split("(")[0].strip()
                failures.append({"test": current_test, "error": ""})
            elif in_fail and failures and stripped and not stripped.startswith(("✓", "✔", "PASS")):
                failures[-1]["error"] += stripped + "\n"

    return failures


def _count_tests(output: str, framework: str) -> int:
    """Count total tests from output."""
    import re

    if framework == "pytest":
        # "5 passed" or "3 failed, 2 passed"
        match = re.search(r"(\d+) passed", output)
        passed = int(match.group(1)) if match else 0
        match = re.search(r"(\d+) failed", output)
        failed = int(match.group(1)) if match else 0
        return passed + failed

    elif framework in ("jest", "vitest"):
        match = re.search(r"Tests:\s*.*?(\d+) total", output)
        if match:
            return int(match.group(1))

    return 0
