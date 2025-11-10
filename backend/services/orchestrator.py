import os
import json
import re
from backend.services.llm_router import get_llm
from backend.services.chunker import chunk_text
from backend.services import repo_scaffold, evaluator
from backend.storage.db import update_job_status, append_job_log
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

SYSTEM_FIXER = "You are a senior maintainer. Given failing output, reply ONLY with fenced code blocks as above. Put test fixes in tests/ directory."


def apply_fenced(repo: str, text: str):
    """Apply fenced code blocks to files and return list of created/modified files"""
    files_created = []
    for header, body in re.findall(r"```(.*?)\n([\s\S]*?)```", text):
        fname = header.strip().split()[0]
        full = os.path.join(repo, fname)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(body)
        files_created.append(fname)
    return files_created


def run_build(job: dict):
    job_id = job['id']
    llm = get_llm()
    
    append_job_log(job_id, 'status', '📋 Creating workspace...')
    repo = repo_scaffold.create_workspace(job)
    append_job_log(job_id, 'status', f'✅ Workspace created: {os.path.basename(repo)}')

    spec_chunks = chunk_text(job["spec"])

    append_job_log(job_id, 'status', '🧠 Planning project structure...')
    plan = llm.complete(system=SYSTEM_PLANNER, user=spec_chunks[0], max_tokens=settings.MAX_REPLY_TOKENS)
    append_job_log(job_id, 'plan', plan)

    append_job_log(job_id, 'status', '💻 Generating code files...')
    for i, ch in enumerate(spec_chunks, 1):
        append_job_log(job_id, 'status', f'   Processing spec chunk {i}/{len(spec_chunks)}...')
        patch = llm.complete(system=SYSTEM_CODER, user=f"SPEC CHUNK:\n{ch}\n\nPLAN:\n{plan}", max_tokens=settings.MAX_REPLY_TOKENS)
        files_created = apply_fenced(repo, patch)
        for fname in files_created:
            with open(os.path.join(repo, fname), 'r') as f:
                content = f.read()
            append_job_log(job_id, 'file', {'path': fname, 'content': content})

    append_job_log(job_id, 'status', '🧪 Running tests...')
    report = None
    for iteration in range(settings.MAX_ITERS):
        ok, report = evaluator.run(repo)
        
        # Log test output
        append_job_log(job_id, 'test', {
            'iteration': iteration + 1,
            'passed': ok,
            'output': report
        })
        
        if ok:
            append_job_log(job_id, 'status', '✅ Build succeeded! All tests passed.')
            update_job_status(job_id, 'succeeded', report)
            return True, repo
        
        append_job_log(job_id, 'status', f'⚠️  Tests failed (attempt {iteration + 1}/{settings.MAX_ITERS}). Applying fixes...')
        fix = llm.complete(system=SYSTEM_FIXER, user=json.dumps(report)[:settings.MAX_INPUT_CHARS], max_tokens=settings.MAX_REPLY_TOKENS)
        files_fixed = apply_fenced(repo, fix)
        for fname in files_fixed:
            append_job_log(job_id, 'status', f'   Fixed: {fname}')

    append_job_log(job_id, 'status', '❌ Build failed after maximum fix attempts.')
    update_job_status(job_id, 'failed', report)
    return False, repo
