# FORGE — Where Concepts Become Systems

A production-ready code generation workbench that turns natural language specifications into working code repositories with automated testing and fixing.

**GitHub Repository**: https://github.com/hoffmv/forge

## Overview

FORGE is a Replit-style application with a 3-pane interface that:
- Generates code from natural language specifications
- Runs automated tests and fixes failures
- Supports dual LLM providers: LM Studio (local) and OpenAI (cloud)
- Provides runtime provider switching via UI toggle
- Delivers as both web app and Electron desktop application

## Architecture

### Monorepo Structure
```
forge/
├── backend/          # FastAPI orchestrator
├── frontend/         # React/Vite 3-pane UI
├── launcher/         # Electron desktop wrapper
└── installers/       # Staged installer scripts
```

### Backend Components
- **Providers**: LM Studio (local) and OpenAI (cloud) LLM integrations
- **Services**: Orchestrator with Planner → Coder → AI Architect → Verifier → Fixer loop
- **AI Architect**: Intelligent code reviewer that finds bugs, architecture issues, and quality problems
- **Storage**: SQLite for job tracking
- **Worker**: Background job processor

### Frontend Components
- **Left Pane**: Projects list, Build form (New/Modify toggle), and Conversational Chat (always visible at bottom)
- **Right Pane**: Tabbed interface with Build Process, Preview, Artifacts, Jobs, Console, and Help viewers

## Branding
- **Name**: FORGE — Where Concepts Become Systems
- **Colors**: Ember #FF6E00, Graphite #1C1C1C, Slate #2B2B2B
- **Theme**: Dark with ember-orange highlights

## Configuration

### Data Storage
- **Windows**: `%APPDATA%\FORGE\` (e.g., C:\Users\Username\AppData\Roaming\FORGE\)
- **Unix/Mac**: `~/.forge/`
- **Contents**: builder.db, workspaces/, .forge_key

### Settings Management
- **UI**: Settings gear icon in left pane opens configuration modal
- **LM Studio URL**: Configurable local LLM endpoint (default: http://localhost:1234/v1)
- **OpenAI API Key**: Encrypted at rest with Fernet cipher, stored in database
- **Precedence**: Database settings → Environment variables → Config defaults

### Environment Variables
- `MODE`: LOCAL or CLOUD (determines default LLM provider)
- `LLM_PROVIDER`: AUTO, LMSTUDIO, or OPENAI
- `LMSTUDIO_BASE_URL`: Local LM Studio endpoint (overridden by settings)
- `OPENAI_API_KEY`: OpenAI API key (overridden by encrypted database setting)
- `FORGE_DATA_DIR`: Custom data directory location (optional)
- `FORGE_ENCRYPTION_KEY`: Custom encryption key (optional, auto-generated if not set)

### Workflow Orchestration (AI-Driven Iterative Refinement)
1. User submits spec via UI
2. Backend creates job (queued status)
3. Worker picks job (running status)
4. Planner creates plan from spec
5. Coder generates files with fenced blocks
6. **Iterative Review Loop** (up to MAX_ITERS):
   - **AI Architect** reviews code for bugs, architecture, and quality issues
   - **Verifier** runs pytest tests
   - If both Architect approves AND tests pass → SUCCESS
   - If either fails → **Fixer** patches issues based on:
     - Architect feedback (specific fixes for each issue)
     - Test failure output (pytest errors)
   - Loop repeats until both Architect and tests are satisfied
7. Final status: succeeded (both approved) or failed (max iterations reached)

## Recent Changes
- **November 14, 2025 (Phase 9)**: AI Architect Review System & Preview Tab ✅ COMPLETE
  - **AI Architect Service**: Intelligent code reviewer analyzes generated code for:
    - Bug detection (syntax errors, logic bugs, runtime errors, edge cases)
    - Architecture review (design patterns, modularity, maintainability)
    - Code quality (best practices, security issues, code smells)
    - Test coverage (comprehensive and meaningful tests)
  - **Iterative AI-Driven Fixing**: System loops through Architect → Tests → Fixer until code is production-ready
  - **Dual Validation**: Code must pass BOTH AI Architect approval AND pytest tests to succeed
  - **Architect Feedback Display**: Build Process tab shows detailed review with severity badges, issue types, and specific fixes
  - **Preview Tab**: New tab displays README or web preview of generated projects
  - **Robust Error Handling**: Fixer always receives actionable context even when Architect returns malformed JSON
  - **Smart Fix Context**: Fixer receives combined feedback from both Architect review and test failures
  - Users now get Replit Agent-quality code with iterative AI-driven refinement until perfect

- **November 10, 2025 (Phase 8)**: Interactive User Manual & Help System ✅ COMPLETE
  - Created comprehensive USER_MANUAL.md covering all features and workflows
  - Added Help tab with three modes: Browse Manual, Search Manual, and Ask AI
  - Browse mode displays full manual with markdown rendering and syntax highlighting
  - Search mode enables keyword search across manual sections with relevance ranking
  - Ask AI mode provides LLM-powered Q&A about FORGE usage and features
  - Backend /help endpoints: /manual (full content), /search (keyword search), /ask (AI assistant)
  - AI assistant uses complete manual as context to answer user questions intelligently
  - Manual covers: getting started, project creation, conversational mode, file upload, export, settings, troubleshooting, and FAQ
  - Users can now get instant help without leaving the application

- **November 10, 2025 (Phase 7)**: Conversational Iteration System ✅ COMPLETE
  - Added projects table and messages table for persistent conversation tracking
  - Created conversational orchestrator with 'create' and 'modify' modes
  - Context-aware modification: reads existing workspace files + conversation history before making changes
  - Backend API endpoints for project management (/projects/ - create, list, get, delete)
  - **Chat UI positioned in left pane (always visible)** - enables real-time collaboration while monitoring build process
  - Projects panel in left pane shows all projects with selection UI
  - Dual-mode build form: "New Project" creates fresh projects, "Modify Selected" iterates on existing ones
  - Fixed pytest import error by setting PYTHONPATH in test runner
  - Fixed ChatTab job state management to pass full job objects
  - Users can now iterate on projects through natural language conversation while simultaneously watching builds, artifacts, and logs

- **November 10, 2025 (Phase 6)**: Artifacts Viewer
  - Added Artifacts tab to view generated code directly in the browser
  - File tree sidebar shows all generated files with icons and sizes
  - Code viewer displays file contents with syntax highlighting
  - Backend endpoints to list workspace files and read file content
  - Security: Path traversal protection ensures files stay within workspace
  - Users can now see and explore their generated code without terminal access

- **November 10, 2025 (Phase 5)**: Replit-Style UI Layout Redesign
  - Reorganized UI to match Replit Agent's intuitive 2-column layout
  - Left pane: Build form + activity feed showing submission history
  - Right pane: Tabbed interface with Build Process, Artifacts, Jobs, and Console tabs
  - Cleaner navigation with top tabs instead of 3-pane horizontal layout
  - Activity feed shows last 5 build submissions with timestamps
  - Auto-selects newly submitted jobs for immediate feedback

- **November 10, 2025 (Phase 4)**: Real-Time Build Process Visibility
  - Added streaming logs to orchestrator showing each step: planning, coding, testing
  - Build Process tab displays chain-of-thought build process in real-time
  - Shows plan JSON, generated files with full content, and test results
  - Auto-scrolls to latest activity with fade-in animations
  - Color-coded log types: status (ember), plan (blue), files (green), tests (red/green)
  - Users can now see EXACTLY what FORGE is doing and what it generated

- **November 10, 2025 (Phase 3)**: Fixed Code Generation and Testing
  - Fixed SYSTEM_CODER and SYSTEM_PLANNER prompts to enforce proper directory structure
  - Tests now correctly placed in tests/ directory (was generating in random paths)
  - Verifier now successfully finds and runs pytest tests
  - Tested with real spec: CLI printing "FORGE" with pytest - succeeded with "1 passed"
  - Workspaces now properly created in AppData directory

- **November 10, 2025 (Phase 2)**: Settings UI and Windows Installer
  - Added Settings modal with gear icon for configuring LM Studio URL and OpenAI API key
  - Implemented encrypted settings storage with Fernet cipher (API keys encrypted at rest)
  - Moved database, workspaces, and encryption key to user's AppData directory
  - Settings precedence: database → env vars → config defaults
  - Created PyInstaller configuration for freezing backend into standalone .exe
  - Updated Electron launcher with production mode detection (app.isPackaged)
  - Configured electron-builder with NSIS installer and resource bundling
  - Created build.py orchestration script for complete Windows packaging pipeline

- **November 10, 2025 (Phase 1)**: Full system tested and operational
  - Fixed worker queue with error handling and graceful failure recovery
  - Fixed Electron launcher CWD issue (now runs from repo root)
  - Configured Vite proxy for seamless frontend-backend communication
  - OpenAI provider integration tested and working
  - Successfully generated and executed Python code from natural language specs
  - Jobs flow correctly through queued → running → succeeded/failed lifecycle
  - Generated artifacts stored in `workspaces/{project-name}_{id}/` directories

## User Preferences
None yet.

## Windows Build Instructions

To build a distributable Windows installer:

```bash
# Install PyInstaller (if not already installed)
pip install pyinstaller

# Build everything (backend + frontend + Electron installer)
python build.py --all --clean

# Or build individual components
python build.py --backend    # Freeze backend only
python build.py --frontend   # Build frontend only
python build.py --electron   # Package Electron app with NSIS installer
```

The installer will be created in `launcher/dist/FORGE Setup X.X.X.exe`

## Next Steps
- Test full Windows build pipeline end-to-end
- Add tokenizer-aware chunking for large specs
- Implement artifact preview in right pane
- Add Mac/Linux build configurations
