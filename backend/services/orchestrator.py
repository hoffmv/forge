import os
import json
import re
from backend.services.llm_router import get_llm
from backend.services.chunker import chunk_text
from backend.services import repo_scaffold, evaluator, architect
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

SYSTEM_FIXER = """You are a senior maintainer. Fix the issues described below.

Reply ONLY with fenced code blocks in this format:
```filename.py
<fixed content here>
```

Put test fixes in tests/ directory. Fix ALL issues mentioned."""


def apply_fenced(repo: str, text: str):
    """Apply fenced code blocks to files and return list of created/modified files"""
    files_created = []
    for header, body in re.findall(r"```(.*?)\n([\s\S]*?)```", text):
        header_parts = header.strip().split()
        if not header_parts:
            # Skip code blocks without a filename
            continue
        fname = header_parts[0]
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

    # Iterative review and test loop
    append_job_log(job_id, 'status', '🔍 Starting AI Architect review and testing...')
    
    test_report = None
    for iteration in range(settings.MAX_ITERS):
        append_job_log(job_id, 'status', f'🔄 Iteration {iteration + 1}/{settings.MAX_ITERS}')
        
        # Step 1: AI Architect Review
        append_job_log(job_id, 'status', '   🏗️  AI Architect reviewing code...')
        review = architect.review_code(repo)
        
        append_job_log(job_id, 'architect', {
            'iteration': iteration + 1,
            'has_issues': review.get('has_issues', False),
            'severity': review.get('severity', 'none'),
            'summary': review.get('summary', ''),
            'issues': review.get('issues', [])
        })
        
        # Step 2: Run Tests
        append_job_log(job_id, 'status', '   🧪 Running tests...')
        tests_ok, test_report = evaluator.run(repo)
        
        append_job_log(job_id, 'test', {
            'iteration': iteration + 1,
            'passed': tests_ok,
            'output': test_report
        })
        
        # Check if both architect and tests are satisfied
        architect_ok = not review.get('has_issues', False)
        
        if architect_ok and tests_ok:
            append_job_log(job_id, 'status', '✅ Build succeeded! AI Architect approved and all tests passed.')
            update_job_status(job_id, 'succeeded', test_report)
            return True, repo
        
        # Prepare fix context
        fix_context = ""
        
        if not architect_ok:
            append_job_log(job_id, 'status', f'   ⚠️  AI Architect found {len(review.get("issues", []))} issue(s) (severity: {review.get("severity", "unknown")})')
            fix_context += architect.format_review_for_fixer(review) + "\n\n"
        
        if not tests_ok:
            append_job_log(job_id, 'status', '   ⚠️  Tests failed')
            fix_context += f"# TEST FAILURES\n\n```\n{json.dumps(test_report)}\n```\n\n"
        
        # Apply fixes
        append_job_log(job_id, 'status', '   🔧 Applying fixes...')
        fix = llm.complete(
            system=SYSTEM_FIXER,
            user=fix_context[:settings.MAX_INPUT_CHARS],
            max_tokens=settings.MAX_REPLY_TOKENS
        )
        files_fixed = apply_fenced(repo, fix)
        
        if files_fixed:
            for fname in files_fixed:
                append_job_log(job_id, 'status', f'      ✏️  Fixed: {fname}')
        else:
            append_job_log(job_id, 'status', '      ⚠️  No files were modified by the fixer')

    append_job_log(job_id, 'status', '❌ Build failed after maximum fix attempts.')
    update_job_status(job_id, 'failed', test_report)
    return False, repo
