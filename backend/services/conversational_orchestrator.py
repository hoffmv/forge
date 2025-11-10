import os
import json
import re
from pathlib import Path
from backend.services.llm_router import get_llm
from backend.services.chunker import chunk_text
from backend.services import repo_scaffold, evaluator
from backend.storage.db import (
    update_job_status, append_job_log, 
    get_project, update_project_workspace, get_messages, add_message
)
from backend.config import settings

SYSTEM_PLANNER = """You are a senior software architect. Plan tasks, files, and tests. Output JSON with keys: files[], tests[], steps[]. 
IMPORTANT: All test files MUST be placed in a tests/ directory at the project root. Keep it compact."""

SYSTEM_CODER = """You are a senior developer. Implement the files using proper project structure.

CRITICAL RULES:
1. ALL test files MUST go in the tests/ directory at project root
2. Use proper file paths (e.g., 'src/main.py', 'tests/test_main.py')
3. For Python projects: put source in root or src/, tests in tests/
4. Reply with fenced code blocks in this format:

```filename.py
<content here>
```

```tests/test_filename.py
<test content here>
```

Repeat for each file. Use REAL file paths, not placeholders."""

SYSTEM_MODIFIER = """You are a senior developer making iterative improvements to an existing codebase.

CONTEXT:
The user has an existing project with specific files and wants you to make targeted changes.

TASK:
1. Review the current codebase structure and files shown below
2. Make ONLY the changes requested by the user
3. Reply with fenced code blocks for ONLY the files you're modifying/adding

Format for code blocks:
```filename.py
<complete updated file content>
```

DO NOT regenerate files that don't need changes. Only output what needs to be modified or added."""

SYSTEM_FIXER = "You are a senior maintainer. Given failing output, reply ONLY with fenced code blocks as above. Put test fixes in tests/ directory."


def apply_fenced(repo: str, text: str):
    """Apply fenced code blocks to files and return list of created/modified files"""
    files_created = []
    for header, body in re.findall(r"```(.*?)\n([\s\S]*?)```", text):
        header_parts = header.strip().split()
        if not header_parts:
            continue
        fname = header_parts[0]
        full = os.path.join(repo, fname)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(body)
        files_created.append(fname)
    return files_created


def get_workspace_context(workspace_path: str) -> str:
    """Get a summary of the current workspace for context-aware modifications"""
    if not workspace_path or not os.path.exists(workspace_path):
        return ""
    
    context_lines = ["CURRENT WORKSPACE STRUCTURE:", ""]
    
    # List all files in workspace
    for root, dirs, files in os.walk(workspace_path):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        level = root.replace(workspace_path, '').count(os.sep)
        indent = '  ' * level
        folder_name = os.path.basename(root) or 'root'
        context_lines.append(f"{indent}{folder_name}/")
        
        sub_indent = '  ' * (level + 1)
        for file in sorted(files):
            if not file.startswith('.'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, workspace_path)
                
                # Include file content for small files
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if len(content) < 2000:  # Only include small files
                        context_lines.append(f"\n--- FILE: {rel_path} ---")
                        context_lines.append(content)
                        context_lines.append("--- END FILE ---\n")
                    else:
                        context_lines.append(f"{sub_indent}{file} ({len(content)} bytes)")
                except:
                    context_lines.append(f"{sub_indent}{file}")
    
    return "\n".join(context_lines)


def build_conversation_context(project_id: str | None) -> str:
    """Build conversation history for context"""
    if not project_id:
        return ""
    messages = get_messages(project_id)
    if not messages:
        return ""
    
    lines = ["CONVERSATION HISTORY:", ""]
    for msg in messages:
        role_label = "USER" if msg['role'] == 'user' else "ASSISTANT"
        lines.append(f"{role_label}: {msg['content']}")
        lines.append("")
    
    return "\n".join(lines)


def run_conversational_build(job: dict, project_id: str | None = None, mode: str = "create"):
    """
    Run a build with conversational context
    
    Args:
        job: The job dict with spec, project_name, etc
        project_id: Optional project ID for iterative builds
        mode: 'create' for initial generation, 'modify' for iterative edits
    """
    job_id = job['id']
    llm = get_llm()
    
    # Create or resume workspace
    if mode == "create" or not project_id:
        append_job_log(job_id, 'status', '📋 Creating new workspace...')
        repo = repo_scaffold.create_workspace(job)
        append_job_log(job_id, 'status', f'✅ Workspace created: {os.path.basename(repo)}')
        
        # Store workspace path in project if project_id provided
        if project_id:
            update_project_workspace(project_id, repo)
            add_message(project_id, 'user', job['spec'], job_id)
    else:
        # Resume existing project
        project = get_project(project_id)
        if not project or not project['workspace_path']:
            raise ValueError(f"Project {project_id} has no workspace")
        
        repo = project['workspace_path']
        append_job_log(job_id, 'status', f'📂 Resuming workspace: {os.path.basename(repo)}')
        add_message(project_id, 'user', job['spec'], job_id)
    
    spec_chunks = chunk_text(job["spec"])
    
    if mode == "create":
        # Initial creation - plan and generate
        append_job_log(job_id, 'status', '🧠 Planning project structure...')
        plan = llm.complete(system=SYSTEM_PLANNER, user=spec_chunks[0], max_tokens=settings.MAX_REPLY_TOKENS)
        append_job_log(job_id, 'plan', plan)
        
        append_job_log(job_id, 'status', '💻 Generating code files...')
        for i, ch in enumerate(spec_chunks, 1):
            append_job_log(job_id, 'status', f'   Processing spec chunk {i}/{len(spec_chunks)}...')
            patch = llm.complete(
                system=SYSTEM_CODER, 
                user=f"SPEC CHUNK:\n{ch}\n\nPLAN:\n{plan}", 
                max_tokens=settings.MAX_REPLY_TOKENS
            )
            files_created = apply_fenced(repo, patch)
            for fname in files_created:
                with open(os.path.join(repo, fname), 'r') as f:
                    content = f.read()
                append_job_log(job_id, 'file', {'path': fname, 'content': content})
    
    else:  # mode == "modify"
        # Iterative modification - read context and make targeted changes
        append_job_log(job_id, 'status', '🔍 Reading current workspace...')
        workspace_context = get_workspace_context(repo)
        conversation_context = build_conversation_context(project_id)
        
        append_job_log(job_id, 'status', '✏️  Making targeted modifications...')
        modification_prompt = f"""{conversation_context}

{workspace_context}

NEW USER REQUEST:
{job['spec']}

Make ONLY the changes needed to fulfill this request. Output fenced code blocks for modified/new files only."""
        
        patch = llm.complete(
            system=SYSTEM_MODIFIER, 
            user=modification_prompt, 
            max_tokens=settings.MAX_REPLY_TOKENS
        )
        
        files_modified = apply_fenced(repo, patch)
        for fname in files_modified:
            with open(os.path.join(repo, fname), 'r') as f:
                content = f.read()
            append_job_log(job_id, 'file', {'path': fname, 'content': content})
        
        append_job_log(job_id, 'status', f'✅ Modified {len(files_modified)} file(s)')
    
    # Run tests and fix if needed
    append_job_log(job_id, 'status', '🧪 Running tests...')
    report = None
    for iteration in range(settings.MAX_ITERS):
        ok, report = evaluator.run(repo)
        
        append_job_log(job_id, 'test', {
            'iteration': iteration + 1,
            'passed': ok,
            'output': report
        })
        
        if ok:
            append_job_log(job_id, 'status', '✅ Build succeeded! All tests passed.')
            update_job_status(job_id, 'succeeded', report)
            
            # Add assistant message to conversation
            if project_id:
                success_msg = f"Successfully {'created' if mode == 'create' else 'modified'} the project. All tests passed!"
                add_message(project_id, 'assistant', success_msg, job_id)
            
            return True, repo
        
        append_job_log(job_id, 'status', f'⚠️  Tests failed (attempt {iteration + 1}/{settings.MAX_ITERS}). Applying fixes...')
        fix = llm.complete(
            system=SYSTEM_FIXER, 
            user=json.dumps(report)[:settings.MAX_INPUT_CHARS], 
            max_tokens=settings.MAX_REPLY_TOKENS
        )
        files_fixed = apply_fenced(repo, fix)
        for fname in files_fixed:
            append_job_log(job_id, 'status', f'   Fixed: {fname}')
    
    append_job_log(job_id, 'status', '❌ Build failed after maximum fix attempts.')
    update_job_status(job_id, 'failed', report)
    
    # Add failure message to conversation
    if project_id:
        failure_msg = f"Build failed after {settings.MAX_ITERS} attempts. Please review the errors and try again."
        add_message(project_id, 'assistant', failure_msg, job_id)
    
    return False, repo
