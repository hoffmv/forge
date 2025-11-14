# FORGE — Where Concepts Become Systems

A production-ready code generation workbench that turns natural language specifications into working code repositories with automated testing, AI-driven code review, and iterative fixing.

![FORGE](https://img.shields.io/badge/FORGE-AI%20Code%20Generator-FF6E00?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi)
![Electron](https://img.shields.io/badge/Electron-Desktop-47848F?style=flat-square&logo=electron)

## 🔥 Features

- **Natural Language to Code**: Describe your project in plain English, get working code
- **AI Architect Review**: Intelligent code reviewer that checks for bugs, architecture issues, and quality problems
- **Iterative AI Fixing**: Automatically fixes code until it passes both AI review AND automated tests
- **Dual LLM Support**: Switch between LM Studio (local) and OpenAI (cloud) at runtime
- **Replit-Style Interface**: 3-pane UI with real-time build process visibility
- **Conversational Iteration**: Modify projects through natural language chat
- **Preview & Artifacts**: View generated code with syntax highlighting
- **Desktop Application**: Runs as standalone Windows app (Electron wrapper)

## 🏗️ Architecture

### Monorepo Structure
```
forge/
├── backend/          # FastAPI orchestrator + LLM providers
│   ├── providers/    # LM Studio & OpenAI integrations
│   ├── services/     # Planner, Coder, Architect, Verifier, Fixer
│   ├── routers/      # API endpoints
│   └── worker/       # Background job processor
├── frontend/         # React + Vite 3-pane UI
│   ├── src/
│   │   ├── components/  # Tabs, forms, viewers
│   │   └── panes/       # Left & right panes
├── launcher/         # Electron desktop wrapper
└── installers/       # Windows installer scripts
```

### AI-Driven Build Process

```
User Spec → Planner → Coder → AI Architect Review
                                      ↓
                               ✓ Approved?
                                      ↓
                           Verifier (pytest) → ✓ Tests Pass?
                                      ↓
                              Both Pass? → SUCCESS
                                      ↓
                                   Failed?
                                      ↓
                              Fixer Patches Code
                                      ↓
                            Loop until perfect
```

**Dual Validation**: Code must pass **BOTH** AI Architect approval **AND** automated tests to succeed.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Git**
- **LM Studio** (optional, for local LLM) or **OpenAI API Key**

### Installation

#### Option 1: Run from Source (Development)

```bash
# Clone the repository
git clone https://github.com/hoffmv/forge.git
cd forge

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Run backend (from repo root)
uvicorn backend.app:app --host 0.0.0.0 --port 8000

# Run frontend (in new terminal)
cd frontend
npm run dev
```

Open your browser to `http://localhost:5000`

#### Option 2: Windows Installer (End Users)

```bash
# Build the complete installer
python build.py --all --clean

# Installer will be created in:
# launcher/dist/FORGE Setup X.X.X.exe
```

Run the installer, then launch FORGE from your Start Menu or Desktop icon.

## 🔄 Update Workflow

### Getting Updates from GitHub

When improvements are made to FORGE, you can update your local installation:

```bash
# Navigate to your FORGE directory
cd C:\path\to\forge

# Pull latest changes from GitHub
git pull origin main

# Update Python dependencies
pip install -r requirements.txt

# Update frontend dependencies
cd frontend
npm install
cd ..
```

### Rebuild Installer (Optional)

If you want a new standalone `.exe`:

```bash
python build.py --all --clean
```

### Run Latest Version

After pulling updates, you can either:

**A. Run from source:**
```bash
# Terminal 1: Backend
uvicorn backend.app:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

**B. Install new build:**
```bash
python build.py --all
# Then run launcher/dist/FORGE Setup X.X.X.exe
```

## ⚙️ Configuration

### Data Storage Locations

**Windows:**
```
%APPDATA%\FORGE\
├── builder.db          # SQLite database
├── workspaces/         # Generated projects
└── .forge_key          # Encryption key
```

**Unix/Mac:**
```
~/.forge/
├── builder.db
├── workspaces/
└── .forge_key
```

### Environment Variables

Create a `.env` file in the backend directory (optional):

```bash
# LLM Provider Selection
MODE=LOCAL                    # LOCAL or CLOUD
LLM_PROVIDER=AUTO             # AUTO, LMSTUDIO, or OPENAI

# LM Studio Configuration
LMSTUDIO_BASE_URL=http://localhost:1234/v1

# OpenAI Configuration (encrypted in database is preferred)
OPENAI_API_KEY=sk-...

# Custom Data Directory (optional)
FORGE_DATA_DIR=/custom/path/to/data

# Custom Encryption Key (optional, auto-generated if not set)
FORGE_ENCRYPTION_KEY=your-custom-key
```

### LM Studio Setup

1. **Download LM Studio**: https://lmstudio.ai
2. **Load a Model**: Recommended models:
   - `openai/gpt-oss-20b` (12GB RAM)
   - `TheBloke/Mistral-7B-Instruct-v0.2-GGUF` (8GB RAM)
   - Any OpenAI-compatible model
3. **Start Server**: 
   - Click "Local Server" tab
   - Click "Start Server"
   - Default: `http://127.0.0.1:1234`
4. **Configure FORGE**:
   - Click Settings gear icon in FORGE
   - Set LM Studio URL: `http://127.0.0.1:1234/v1`
   - Select "LMSTUDIO" provider

### OpenAI Setup

1. **Get API Key**: https://platform.openai.com/api-keys
2. **Configure in FORGE**:
   - Click Settings gear icon
   - Enter your OpenAI API key
   - Keys are encrypted at rest with Fernet cipher
   - Select "OPENAI" provider

## 🎯 Usage

### Creating a New Project

1. **Enter Project Name**: e.g., "weather-cli"
2. **Write Specification**:
   ```
   Build a Python CLI that fetches current weather for a city.
   Use OpenWeatherMap API. Include pytest tests.
   Requirements: argparse for CLI, requests for API calls.
   ```
3. **Click "Create Project"**
4. **Watch the Build Process**:
   - 📋 Planning: AI creates project structure
   - 💻 Coding: AI generates all files
   - 🏗️ Architect Review: AI checks for bugs/quality issues
   - 🧪 Testing: pytest validates functionality
   - 🔧 Fixing: AI patches any issues (if needed)
   - ✅ Success: Both AI and tests approve!

### Modifying an Existing Project

1. **Select Project** from the Projects panel
2. **Click "Modify Selected"** toggle
3. **Describe Changes**:
   ```
   Add a --forecast flag to show 5-day forecast
   ```
4. **Submit**: FORGE reads existing code + conversation history and makes intelligent changes

### Viewing Generated Code

- **Build Process Tab**: Real-time logs showing what AI is doing
- **Preview Tab**: README or web preview of project
- **Artifacts Tab**: File tree with syntax-highlighted code viewer
- **Jobs Tab**: History of all builds
- **Console Tab**: Backend logs and errors

### Exporting Projects

Generated projects are saved to:
- **Replit**: `/home/runner/workspace/workspaces/project-name_id/`
- **Windows**: `%APPDATA%\FORGE\workspaces\project-name_id\`

Access files directly or use the Artifacts tab to browse and copy code.

## 🛠️ Development

### Project Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: React 18, Vite, CSS3
- **Desktop**: Electron, electron-builder
- **LLMs**: OpenAI API, LM Studio (OpenAI-compatible)
- **Packaging**: PyInstaller, NSIS

### Building Components

```bash
# Backend executable only
python build.py --backend

# Frontend bundle only
python build.py --frontend

# Electron installer only
python build.py --electron

# Everything
python build.py --all --clean
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend (no tests yet)
cd frontend
npm run test
```

## 🎨 Branding

- **Name**: FORGE — Where Concepts Become Systems
- **Colors**: 
  - Ember: `#FF6E00` (primary)
  - Graphite: `#1C1C1C` (background)
  - Slate: `#2B2B2B` (surfaces)
- **Theme**: Dark mode with ember-orange highlights

## 📦 System Requirements

### Minimum
- **OS**: Windows 10+ (installer), Linux/Mac (source)
- **RAM**: 8GB (16GB+ recommended for LM Studio)
- **Storage**: 2GB + space for generated projects
- **GPU**: Optional (accelerates LM Studio)

### Recommended
- **RAM**: 16GB+
- **GPU**: NVIDIA GPU with 8GB+ VRAM (for local LLMs)
- **Storage**: 50GB+ (for LM Studio models)

## 🐛 Troubleshooting

### LM Studio Connection Refused

**Problem**: `Connection refused: localhost:1234`

**Solution**:
1. Verify LM Studio server is running (green "Running" status)
2. Check URL in Settings matches LM Studio (default: `http://127.0.0.1:1234/v1`)
3. Ensure model is loaded in LM Studio
4. If running FORGE on Replit, use OpenAI instead (cloud can't reach localhost)

### OpenAI API Errors

**Problem**: `Invalid API key` or `Rate limit exceeded`

**Solution**:
1. Verify API key at https://platform.openai.com/api-keys
2. Check billing/credits in OpenAI dashboard
3. Update key in FORGE Settings

### Build Process Stuck

**Problem**: Job stays in "running" status indefinitely

**Solution**:
1. Check Console tab for errors
2. Verify LLM provider is responding
3. Check network connectivity
4. Restart FORGE

### Artifacts Tab Empty

**Problem**: Build succeeded but no files visible

**Solution**:
1. Check Build Process tab for generated files
2. Navigate to workspace directory manually
3. Check backend logs for workspace creation errors

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

- **GitHub Issues**: https://github.com/hoffmv/forge/issues
- **Documentation**: See `USER_MANUAL.md` for detailed usage guide

---

**Built with ❤️ and AI**
