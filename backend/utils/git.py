"""
Git subprocess wrapper for GitHub integration.
Handles init, add, commit, push operations.
"""
import subprocess
import os
from backend.utils.logger import log_action, log_error


def _run_git(args: list[str], cwd: str) -> dict:
    """Run a git command and return result."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {"success": False, "stdout": "", "stderr": "git not found on PATH", "returncode": -1}
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "git command timed out", "returncode": -1}


def is_git_repo(project_path: str) -> bool:
    """Check if directory is already a git repository."""
    return os.path.isdir(os.path.join(project_path, ".git"))


def init(project_path: str) -> dict:
    """Initialize a git repo if not already one."""
    if is_git_repo(project_path):
        log_action("git", "Already a git repo", {"path": project_path})
        return {"success": True, "detail": "Already initialized"}

    result = _run_git(["init"], cwd=project_path)
    if result["success"]:
        log_action("git", "Initialized repo", {"path": project_path})

        # Create .gitignore if missing
        gitignore_path = os.path.join(project_path, ".gitignore")
        if not os.path.exists(gitignore_path):
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write("__pycache__/\n*.pyc\nnode_modules/\n.env\n*.egg-info/\ndist/\nbuild/\n.venv/\nvenv/\n")
    else:
        log_error("git", "init failed", result)
    return result


def add_all(project_path: str) -> dict:
    """Stage all changes."""
    result = _run_git(["add", "-A"], cwd=project_path)
    if result["success"]:
        log_action("git", "Staged all changes")
    else:
        log_error("git", "add failed", result)
    return result


def commit(project_path: str, message: str) -> dict:
    """Create a commit with the given message."""
    result = _run_git(["commit", "-m", message], cwd=project_path)
    if result["success"]:
        log_action("git", f"Committed: {message[:80]}")
    elif "nothing to commit" in result["stdout"] + result["stderr"]:
        return {"success": True, "detail": "Nothing to commit", "stdout": result["stdout"], "stderr": result["stderr"]}
    else:
        log_error("git", "commit failed", result)
    return result


def add_remote(project_path: str, repo_url: str) -> dict:
    """Set or update the 'origin' remote."""
    # Check if origin exists
    check = _run_git(["remote", "get-url", "origin"], cwd=project_path)
    if check["success"]:
        # Update existing remote
        result = _run_git(["remote", "set-url", "origin", repo_url], cwd=project_path)
    else:
        # Add new remote
        result = _run_git(["remote", "add", "origin", repo_url], cwd=project_path)

    if result["success"]:
        log_action("git", f"Remote set to {repo_url}")
    else:
        log_error("git", "remote setup failed", result)
    return result


def push(project_path: str, branch: str = "main") -> dict:
    """Push to origin."""
    result = _run_git(["push", "-u", "origin", branch], cwd=project_path)
    if result["success"]:
        log_action("git", f"Pushed to origin/{branch}")
    else:
        # Try setting upstream on first push
        if "has no upstream" in result["stderr"] or "set-upstream" in result["stderr"]:
            result = _run_git(["push", "--set-upstream", "origin", branch], cwd=project_path)
        if not result["success"]:
            log_error("git", "push failed", result)
    return result


def full_push(project_path: str, repo_url: str, message: str = "Forge build", token: str = None) -> dict:
    """
    Full git workflow: init → add → commit → set remote → push.
    If token is provided, inject it into the HTTPS URL for auth.
    """
    # Inject token into URL if provided
    if token and repo_url.startswith("https://"):
        # https://github.com/user/repo → https://TOKEN@github.com/user/repo
        auth_url = repo_url.replace("https://", f"https://{token}@", 1)
    else:
        auth_url = repo_url

    steps = []

    # Init
    r = init(project_path)
    steps.append({"step": "init", **r})
    if not r["success"]:
        return {"success": False, "detail": "git init failed", "steps": steps}

    # Add
    r = add_all(project_path)
    steps.append({"step": "add", **r})
    if not r["success"]:
        return {"success": False, "detail": "git add failed", "steps": steps}

    # Commit
    r = commit(project_path, message)
    steps.append({"step": "commit", **r})

    # Remote
    r = add_remote(project_path, auth_url)
    steps.append({"step": "remote", **r})
    if not r["success"]:
        return {"success": False, "detail": "git remote failed", "steps": steps}

    # Push
    r = push(project_path)
    steps.append({"step": "push", **r})
    if not r["success"]:
        return {"success": False, "detail": f"git push failed: {r.get('stderr', '')}", "steps": steps}

    log_action("git", f"Full push complete to {repo_url}")
    return {"success": True, "detail": f"Pushed to {repo_url}", "steps": steps}
