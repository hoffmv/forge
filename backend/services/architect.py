"""
AI Architect Service - Reviews code for bugs, architecture issues, and quality
"""
import os
import json
from backend.services.llm_router import get_llm
from backend.config import settings

SYSTEM_ARCHITECT = """You are a senior software architect and code reviewer with expertise in finding bugs, architectural issues, and code quality problems.

Your role is to thoroughly review code and provide SPECIFIC, ACTIONABLE feedback:

1. **Bug Detection**: Find syntax errors, logic bugs, runtime errors, edge cases
2. **Architecture Review**: Check design patterns, modularity, maintainability
3. **Code Quality**: Identify code smells, best practices violations, security issues
4. **Test Coverage**: Ensure tests are comprehensive and meaningful

OUTPUT FORMAT (JSON):
{
  "has_issues": true/false,
  "severity": "critical" | "major" | "minor" | "none",
  "issues": [
    {
      "file": "path/to/file.py",
      "line": 42,
      "type": "bug" | "architecture" | "quality" | "test",
      "severity": "critical" | "major" | "minor",
      "description": "Specific problem description",
      "fix": "Exact steps to fix this issue"
    }
  ],
  "summary": "Overall assessment and recommendations"
}

Be thorough but concise. Focus on REAL issues, not stylistic preferences.
If the code is production-ready, return has_issues: false.
"""


def review_code(repo_path: str) -> dict:
    """
    Review all code in the repository using AI Architect
    Returns: dict with has_issues, severity, issues[], summary
    """
    llm = get_llm()
    
    # Collect all code files
    code_files = []
    for root, dirs, files in os.walk(repo_path):
        # Skip common ignore dirs
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', 'venv', '.venv'}]
        
        for file in files:
            if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs')):
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, repo_path)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    code_files.append({
                        'path': relpath,
                        'content': content
                    })
                except Exception:
                    continue
    
    if not code_files:
        return {
            'has_issues': False,
            'severity': 'none',
            'issues': [],
            'summary': 'No code files found to review'
        }
    
    # Prepare review context
    context = "# CODE REVIEW REQUEST\n\n"
    for cf in code_files:
        context += f"## File: {cf['path']}\n```\n{cf['content']}\n```\n\n"
    
    # Truncate if too large
    if len(context) > settings.MAX_INPUT_CHARS:
        context = context[:settings.MAX_INPUT_CHARS] + "\n... (truncated)"
    
    # Get AI review
    review_text = llm.complete(
        system=SYSTEM_ARCHITECT,
        user=context,
        max_tokens=settings.MAX_REPLY_TOKENS
    )
    
    # Parse JSON response
    try:
        review = json.loads(review_text)
    except json.JSONDecodeError:
        # Fallback if LLM doesn't return valid JSON
        review = {
            'has_issues': True,
            'severity': 'unknown',
            'issues': [],
            'summary': review_text[:500]
        }
    
    return review


def format_review_for_fixer(review: dict) -> str:
    """
    Format architect review into actionable instructions for the Fixer
    Always includes summary to ensure Fixer has context even if issues array is empty
    """
    if not review.get('has_issues'):
        return ""
    
    output = "# AI ARCHITECT REVIEW FINDINGS\n\n"
    output += f"**Severity**: {review.get('severity', 'unknown')}\n"
    output += f"**Summary**: {review.get('summary', 'Issues found')}\n\n"
    
    issues = review.get('issues', [])
    
    if issues:
        # Structured issues available
        output += "## Specific Issues to Fix:\n\n"
        for i, issue in enumerate(issues, 1):
            output += f"### Issue {i}: {issue.get('description', 'Unknown issue')}\n"
            output += f"- **File**: {issue.get('file', 'unknown')}\n"
            output += f"- **Line**: {issue.get('line', 'N/A')}\n"
            output += f"- **Type**: {issue.get('type', 'unknown')}\n"
            output += f"- **Severity**: {issue.get('severity', 'unknown')}\n"
            output += f"- **Fix**: {issue.get('fix', 'No fix provided')}\n\n"
    else:
        # No structured issues - ensure summary is included so Fixer has actionable content
        output += "## Review Notes:\n\n"
        output += "The AI Architect flagged issues but did not provide structured details.\n"
        output += "Review the summary above carefully and address all mentioned problems.\n\n"
        output += "**Important**: Fix all issues mentioned in the summary, paying special attention to:\n"
        output += "- Syntax errors and runtime bugs\n"
        output += "- Logic errors and edge cases\n"
        output += "- Code quality and best practices\n"
        output += "- Test coverage gaps\n\n"
    
    return output
