"""
All LLM prompt templates for Forge.
"""

AUDIT_PROMPT = """You are Forge, an autonomous build agent. Analyze this project completely.

Project files:
{full_file_dump}

Task: {task_description}

Return a JSON build plan:
{{
  "project_type": "...",
  "detected_issues": [...],
  "build_plan": [
    {{"action": "create|edit|delete", "file": "path", "instruction": "what to do"}}
  ]
}}
Return JSON only. No explanation."""

FIX_PROMPT = """You are Forge. A build error occurred. Fix it.

Error:
{error_output}

Relevant files:
{relevant_file_contents}

Return a JSON patch:
{{
  "file": "relative/path/to/file",
  "patch_type": "replace_lines|full_rewrite|insert_after",
  "target": "exact string to find (for replace) or line number",
  "replacement": "new content"
}}
Return JSON only. No explanation."""

BUILD_PROMPT = """You are Forge, an autonomous build agent. Generate or modify the following file.

Current project files:
{full_file_dump}

Task: {task_description}

Action to perform:
{action_instruction}

Return ONLY the complete file content. No explanation, no markdown fences, no filename header — just the raw file content."""

ALTERNATE_FIX_PROMPT = """You are Forge. Previous fix attempts for this error have failed repeatedly.
The same error keeps occurring. Try a completely different approach.

Error (seen {occurrences} times):
{error_output}

Previous fix attempts:
{previous_fixes}

Current relevant files:
{relevant_file_contents}

Think of an alternative solution. Return a JSON patch:
{{
  "file": "relative/path/to/file",
  "patch_type": "replace_lines|full_rewrite|insert_after",
  "target": "exact string to find (for replace) or line number",
  "replacement": "new content"
}}
Return JSON only. No explanation."""

DIAGNOSE_PROMPT = """You are Forge, an autonomous build agent. A build/test error occurred.
Analyze the error and determine which file(s) need to be fixed.

Error output:
{error_output}

Project file map:
{file_map_summary}

Full contents of likely relevant files:
{relevant_file_contents}

Return a JSON array of patches to apply:
[
  {{
    "file": "relative/path/to/file",
    "patch_type": "replace_lines|full_rewrite|insert_after",
    "target": "exact string to find (for replace) or line number",
    "replacement": "new content"
  }}
]
Return JSON only. No explanation."""
