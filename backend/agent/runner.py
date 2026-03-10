"""
Subprocess build/test executor — runs project commands and captures output.
"""
import os
import subprocess
import json
from backend.utils.logger import log_action, log_error


def detect_run_command(project_path: str) -> dict:
    """
    Detect the appropriate command to run/build a project.

    Returns:
        {"command": [str], "language": str, "detail": str}
    """
    # Python project
    if os.path.exists(os.path.join(project_path, "requirements.txt")) or \
       os.path.exists(os.path.join(project_path, "pyproject.toml")):

        # Look for main entry points in common locations
        for candidate in ["main.py", "app.py", "src/main.py", "src/app.py",
                          "app/main.py", "app/app.py", "server.py", "run.py"]:
            if os.path.exists(os.path.join(project_path, candidate)):
                return {
                    "command": ["python", candidate],
                    "language": "python",
                    "detail": f"Python project, entry: {candidate}",
                }

        # Syntax-check all Python files individually
        py_files = []
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in {"__pycache__", ".venv", "venv", "node_modules"}]
            for f in files:
                if f.endswith(".py"):
                    rel = os.path.relpath(os.path.join(root, f), project_path)
                    py_files.append(rel)

        if py_files:
            # Check syntax of each file
            return {
                "command": ["python", "-c", "; ".join(f"compile(open(r'{f}').read(), r'{f}', 'exec')" for f in py_files[:10])],
                "language": "python",
                "detail": f"Python project, syntax check on {len(py_files)} file(s)",
            }

        return {
            "command": [],
            "language": "python",
            "detail": "Python project, no .py files found to check",
        }

    # Node.js project
    if os.path.exists(os.path.join(project_path, "package.json")):
        try:
            with open(os.path.join(project_path, "package.json"), "r") as f:
                pkg = json.load(f)
            scripts = pkg.get("scripts", {})
            if "build" in scripts:
                return {
                    "command": ["npm", "run", "build"],
                    "language": "javascript",
                    "detail": "Node.js project, npm run build",
                }
            if "start" in scripts:
                return {
                    "command": ["npm", "start"],
                    "language": "javascript",
                    "detail": "Node.js project, npm start",
                }
        except Exception:
            pass

        return {
            "command": ["node", "--check", "."],
            "language": "javascript",
            "detail": "Node.js project, syntax check",
        }

    return {
        "command": [],
        "language": "unknown",
        "detail": "Unknown project type — no recognizable entry point",
    }


def install_dependencies(project_path: str) -> dict:
    """
    Install project dependencies if dependency files are present.

    Returns:
        {"success": bool, "stdout": str, "stderr": str, "detail": str}
    """
    results = []

    # Python deps
    req_file = os.path.join(project_path, "requirements.txt")
    if os.path.exists(req_file):
        log_action("runner", "Installing Python dependencies")
        try:
            result = subprocess.run(
                ["pip", "install", "-r", "requirements.txt", "--quiet"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )
            results.append({
                "type": "python",
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
            })
        except Exception as e:
            results.append({"type": "python", "success": False, "stderr": str(e)})

    # Node deps
    pkg_file = os.path.join(project_path, "package.json")
    if os.path.exists(pkg_file):
        log_action("runner", "Installing Node.js dependencies")
        try:
            result = subprocess.run(
                ["npm", "install", "--silent"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )
            results.append({
                "type": "javascript",
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
            })
        except Exception as e:
            results.append({"type": "javascript", "success": False, "stderr": str(e)})

    if not results:
        return {"success": True, "detail": "No dependency files found"}

    all_ok = all(r["success"] for r in results)
    return {
        "success": all_ok,
        "detail": f"Installed deps: {', '.join(r['type'] for r in results)}",
        "results": results,
    }


def run(project_path: str) -> dict:
    """
    Run the project and capture output.

    Returns:
        {
            "success": bool,
            "exit_code": int,
            "stdout": str,
            "stderr": str,
            "error_type": str | None,
            "error_location": str | None,
        }
    """
    run_info = detect_run_command(project_path)

    if not run_info["command"]:
        log_action("runner", "No run command detected — treating as success")
        return {
            "success": True,
            "exit_code": 0,
            "stdout": "No entry point detected. Skipping run.",
            "stderr": "",
            "error_type": None,
            "error_location": None,
        }

    log_action("runner", f"Running: {' '.join(run_info['command'])}", {"cwd": project_path})

    # Set PYTHONPATH so imports within the project work
    env = os.environ.copy()
    env["PYTHONPATH"] = project_path

    try:
        result = subprocess.run(
            run_info["command"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )

        success = result.returncode == 0
        error_type = None
        error_location = None

        if not success:
            # Try to extract error type and location from stderr
            stderr = result.stderr
            error_type, error_location = _parse_error(stderr, run_info["language"])

        return {
            "success": success,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error_type": error_type,
            "error_location": error_location,
        }

    except subprocess.TimeoutExpired:
        log_error("runner", "Process timed out after 60 seconds")
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "Process timed out after 60 seconds",
            "error_type": "timeout",
            "error_location": None,
        }
    except Exception as e:
        log_error("runner", str(e))
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "error_type": "execution_error",
            "error_location": None,
        }


def _parse_error(stderr: str, language: str) -> tuple[str | None, str | None]:
    """Extract error type and location from stderr output."""
    if not stderr:
        return None, None

    error_type = None
    error_location = None

    if language == "python":
        # Look for Python traceback patterns
        lines = stderr.strip().split("\n")
        for line in reversed(lines):
            line = line.strip()
            # Error type line: "SyntaxError: ...", "ImportError: ..."
            if "Error:" in line or "Exception:" in line:
                error_type = line.split(":")[0].strip()
                break
        # Location: 'File "xxx", line N'
        for line in lines:
            if 'File "' in line and ", line " in line:
                error_location = line.strip()

    elif language in ("javascript", "typescript"):
        lines = stderr.strip().split("\n")
        for line in lines:
            if "SyntaxError" in line or "ReferenceError" in line or "TypeError" in line:
                error_type = line.split(":")[0].strip()
            if "at " in line and ":" in line:
                error_location = line.strip()
                break

    return error_type, error_location
