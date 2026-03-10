import os
import re
from pathlib import Path
from backend.utils.logger import log_action, log_error

# File extensions to language mapping
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".sql": "sql",
    ".sh": "shell",
    ".bat": "batch",
    ".ps1": "powershell",
}

# Directories to always skip
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    ".next", ".nuxt", "dist", "build", ".cache", ".tox", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "egg-info",
}

# Binary / non-text extensions to skip
SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib", ".o", ".a",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".db", ".sqlite", ".sqlite3",
    ".lock",
}

# Import patterns per language
IMPORT_PATTERNS = {
    "python": [
        re.compile(r"^import\s+([\w.]+)", re.MULTILINE),
        re.compile(r"^from\s+([\w.]+)\s+import", re.MULTILINE),
    ],
    "javascript": [
        re.compile(r"""import\s+.*?from\s+['"](.*?)['"]""", re.MULTILINE),
        re.compile(r"""require\(['"](.*?)['"]\)""", re.MULTILINE),
    ],
    "typescript": [
        re.compile(r"""import\s+.*?from\s+['"](.*?)['"]""", re.MULTILINE),
        re.compile(r"""require\(['"](.*?)['"]\)""", re.MULTILINE),
    ],
}

# Export patterns per language
EXPORT_PATTERNS = {
    "python": [
        re.compile(r"^def\s+(\w+)", re.MULTILINE),
        re.compile(r"^class\s+(\w+)", re.MULTILINE),
    ],
    "javascript": [
        re.compile(r"export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)", re.MULTILINE),
        re.compile(r"module\.exports\s*=", re.MULTILINE),
    ],
    "typescript": [
        re.compile(r"export\s+(?:default\s+)?(?:function|class|const|let|var|interface|type)\s+(\w+)", re.MULTILINE),
    ],
}


def detect_language(filepath: str) -> str:
    """Detect language from file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    return LANGUAGE_MAP.get(ext, "unknown")


def extract_imports(content: str, language: str) -> list[str]:
    """Extract import statements from file content."""
    imports = []
    for pattern in IMPORT_PATTERNS.get(language, []):
        imports.extend(pattern.findall(content))
    return sorted(set(imports))


def extract_exports(content: str, language: str) -> list[str]:
    """Extract exported symbols from file content."""
    exports = []
    for pattern in EXPORT_PATTERNS.get(language, []):
        exports.extend(pattern.findall(content))
    return sorted(set(exports))


def infer_purpose(filepath: str, content: str, language: str) -> str:
    """Infer the purpose of a file from its name, path, and content."""
    name = os.path.basename(filepath).lower()
    rel_parts = filepath.replace("\\", "/").lower()

    if "test" in name or "/tests/" in rel_parts:
        return "test"
    if name in ("readme.md", "readme.txt", "readme.rst"):
        return "documentation"
    if name in ("setup.py", "setup.cfg", "pyproject.toml", "package.json", "cargo.toml"):
        return "config"
    if name in ("requirements.txt", "pipfile", "gemfile", "go.mod"):
        return "dependencies"
    if name in (".env", ".env.example", ".env.local"):
        return "environment"
    if name in ("dockerfile", "docker-compose.yml", "docker-compose.yaml"):
        return "infrastructure"
    if name.endswith((".html", ".css", ".scss")):
        return "frontend"
    if "main" in name or "app" in name or "server" in name:
        return "entry_point"
    if "model" in name or "schema" in name:
        return "data_model"
    if "route" in name or "router" in name or "view" in name or "controller" in name:
        return "routing"
    if "util" in name or "helper" in name or "lib" in name:
        return "utility"

    return "source"


def scan(project_path: str) -> dict:
    """
    Recursively scan a project directory and build a complete file map.

    Returns:
        {
            "project_path": str,
            "project_type": "python" | "javascript" | "mixed" | "unknown",
            "file_count": int,
            "file_map": {
                "relative/path/to/file": {
                    "purpose": str,
                    "language": str,
                    "imports": [str],
                    "exports": [str],
                    "size_bytes": int,
                    "lines": int,
                }
            },
            "detected_issues": [str],
            "dependencies": {"python": [...], "javascript": [...]},
        }
    """
    project_path = os.path.abspath(project_path)
    if not os.path.isdir(project_path):
        log_error("auditor", f"Path does not exist or is not a directory: {project_path}")
        return {
            "project_path": project_path,
            "project_type": "unknown",
            "file_count": 0,
            "file_map": {},
            "detected_issues": [f"Directory not found: {project_path}"],
            "dependencies": {},
        }

    log_action("auditor", f"Scanning project: {project_path}")

    file_map: dict[str, dict] = {}
    language_counts: dict[str, int] = {}
    issues: list[str] = []
    deps: dict[str, list[str]] = {}

    for root, dirs, files in os.walk(project_path):
        # Prune skip directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in SKIP_EXTENSIONS:
                continue

            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, project_path).replace("\\", "/")

            language = detect_language(filepath)
            language_counts[language] = language_counts.get(language, 0) + 1

            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception as e:
                issues.append(f"Cannot read {rel_path}: {e}")
                continue

            imports = extract_imports(content, language)
            exports = extract_exports(content, language)
            purpose = infer_purpose(rel_path, content, language)
            line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

            file_map[rel_path] = {
                "purpose": purpose,
                "language": language,
                "imports": imports,
                "exports": exports,
                "size_bytes": len(content.encode("utf-8")),
                "lines": line_count,
            }

    # Detect project type from language distribution
    code_langs = {k: v for k, v in language_counts.items() if k not in ("unknown", "json", "yaml", "toml", "markdown")}
    if not code_langs:
        project_type = "unknown"
    elif len(code_langs) == 1:
        project_type = list(code_langs.keys())[0]
    else:
        top = sorted(code_langs.items(), key=lambda x: x[1], reverse=True)
        if top[0][1] > sum(v for _, v in top[1:]):
            project_type = top[0][0]
        else:
            project_type = "mixed"

    # Detect dependency files
    if "requirements.txt" in file_map:
        req_path = os.path.join(project_path, "requirements.txt")
        try:
            with open(req_path, "r") as f:
                deps["python"] = [line.strip().split("==")[0].split(">=")[0].split("<=")[0]
                                  for line in f if line.strip() and not line.startswith("#")]
        except Exception:
            pass

    if "package.json" in file_map:
        pkg_path = os.path.join(project_path, "package.json")
        try:
            import json
            with open(pkg_path, "r") as f:
                pkg = json.load(f)
            deps["javascript"] = list(pkg.get("dependencies", {}).keys())
        except Exception:
            pass

    # Check for common issues
    py_files = [k for k, v in file_map.items() if v["language"] == "python"]
    if py_files and "requirements.txt" not in file_map and "pyproject.toml" not in file_map:
        issues.append("Python project missing requirements.txt or pyproject.toml")

    js_files = [k for k, v in file_map.items() if v["language"] in ("javascript", "typescript")]
    if js_files and "package.json" not in file_map:
        issues.append("JavaScript/TypeScript project missing package.json")

    log_action("auditor", f"Scan complete: {len(file_map)} files, type={project_type}", {
        "issues": len(issues),
        "languages": language_counts,
    })

    return {
        "project_path": project_path,
        "project_type": project_type,
        "file_count": len(file_map),
        "file_map": file_map,
        "detected_issues": issues,
        "dependencies": deps,
    }


def get_full_dump(project_path: str) -> str:
    """
    Read every file in the project and return a single string dump
    suitable for inclusion in an LLM prompt.
    """
    scan_result = scan(project_path)
    parts = []
    for rel_path, info in sorted(scan_result["file_map"].items()):
        full_path = os.path.join(project_path, rel_path)
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            parts.append(f"=== FILE: {rel_path} ({info['language']}) ===\n{content}\n")
        except Exception:
            parts.append(f"=== FILE: {rel_path} (unreadable) ===\n")

    return "\n".join(parts)
