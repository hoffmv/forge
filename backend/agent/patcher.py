"""
Targeted file patch applier — applies patches without full-file rewrites.
Supports: replace_lines, full_rewrite, insert_after
"""
import os
from backend.utils.logger import log_action, log_error


def apply(project_path: str, patch: dict) -> dict:
    """
    Apply a single patch to a file.

    Args:
        project_path: Absolute path to the project root.
        patch: Dict with keys:
            - file: relative path
            - patch_type: "replace_lines" | "full_rewrite" | "insert_after"
            - target: string to find (replace_lines) or line number (insert_after)
            - replacement: new content

    Returns:
        {"success": bool, "file": str, "detail": str}
    """
    rel_file = patch.get("file", "")
    patch_type = patch.get("patch_type", "full_rewrite")
    target = patch.get("target", "")
    replacement = patch.get("replacement", "")

    if not rel_file:
        return {"success": False, "file": rel_file, "detail": "No file specified in patch"}

    filepath = os.path.join(project_path, rel_file)
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

    try:
        if patch_type == "full_rewrite":
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(replacement)
            log_action("patcher", f"Full rewrite: {rel_file}")
            return {"success": True, "file": rel_file, "detail": "Full rewrite applied"}

        elif patch_type == "replace_lines":
            if not os.path.exists(filepath):
                # File doesn't exist — treat as full_rewrite
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(replacement)
                log_action("patcher", f"Created new file (replace_lines fallback): {rel_file}")
                return {"success": True, "file": rel_file, "detail": "File created (target not applicable)"}

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if str(target) not in content:
                # Target string not found — log warning and do full rewrite
                log_error("patcher", f"Target string not found in {rel_file}, falling back to full rewrite")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(replacement)
                return {"success": True, "file": rel_file, "detail": "Target not found, full rewrite fallback"}

            new_content = content.replace(str(target), replacement, 1)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            log_action("patcher", f"Replace applied in: {rel_file}")
            return {"success": True, "file": rel_file, "detail": "Replace applied"}

        elif patch_type == "insert_after":
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(replacement)
                log_action("patcher", f"Created new file (insert_after fallback): {rel_file}")
                return {"success": True, "file": rel_file, "detail": "File created (no existing content)"}

            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # target can be a line number or a string to find
            insert_idx = None
            try:
                line_num = int(target)
                insert_idx = min(line_num, len(lines))
            except (ValueError, TypeError):
                # Find the line containing the target string
                for i, line in enumerate(lines):
                    if str(target) in line:
                        insert_idx = i + 1
                        break

            if insert_idx is None:
                # Append to end
                insert_idx = len(lines)

            lines.insert(insert_idx, replacement if replacement.endswith("\n") else replacement + "\n")

            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(lines)

            log_action("patcher", f"Inserted after line {insert_idx} in: {rel_file}")
            return {"success": True, "file": rel_file, "detail": f"Inserted after line {insert_idx}"}

        else:
            return {"success": False, "file": rel_file, "detail": f"Unknown patch_type: {patch_type}"}

    except Exception as e:
        log_error("patcher", f"Failed to patch {rel_file}: {e}")
        return {"success": False, "file": rel_file, "detail": str(e)}


def apply_multiple(project_path: str, patches: list[dict]) -> list[dict]:
    """Apply a list of patches and return results for each."""
    return [apply(project_path, p) for p in patches]
