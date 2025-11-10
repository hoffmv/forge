# FORGE Deployment Guide

## 📍 Where Your Generated Code Lives

### Development/Testing (Current Environment)
When FORGE generates code, it's stored in:

**Windows:** `C:\Users\YourUsername\AppData\Roaming\FORGE\workspaces\`

**Unix/Mac:** `~/.forge/workspaces/`

Each project gets its own directory: `{project-name}_{unique-id}/`

### Accessing Your Generated Code

FORGE provides **3 ways** to access your generated projects:

#### 1. 📥 Download as ZIP (Recommended)
- Go to **Artifacts tab** after a successful build
- Click **"📥 Download as ZIP"** button
- Extract the ZIP anywhere you want
- Ready to run or deploy!

#### 2. 📂 Copy Workspace Path
- Go to **Artifacts tab** after a successful build  
- Click **"📂 Copy Workspace Path"** button
- Opens File Explorer to the exact location
- Manually copy files where you need them

#### 3. 🔍 Direct Filesystem Access
- Navigate to `%APPDATA%\FORGE\workspaces\` on Windows
- Find your project folder by name
- Copy the entire folder to your desired location

---

## 🚀 Windows Installer Build Process

FORGE can be packaged as a standalone Windows installer (`.exe`) for distribution.

### Prerequisites
```bash
# Python packages
pip install pyinstaller

# Node.js/npm installed
# Electron builder dependencies
cd launcher && npm install
```

### Build Commands

#### Full Build (Recommended)
Creates complete Windows installer with everything bundled:
```bash
python build.py --all --clean
```

This will:
1. ✅ Freeze backend Python code → `forge-backend.exe`
2. ✅ Build React frontend → Production static files
3. ✅ Package Electron app → Desktop wrapper
4. ✅ Create NSIS installer → `FORGE Setup X.X.X.exe`

**Output:** `launcher/dist/FORGE Setup X.X.X.exe`

#### Individual Build Steps

**Backend only:**
```bash
python build.py --backend
```

**Frontend only:**
```bash
python build.py --frontend
```

**Electron package only** (requires backend + frontend built first):
```bash
python build.py --electron
```

---

## 📦 What Gets Installed

When users install FORGE on Windows:

```
C:\Users\{Username}\AppData\Local\Programs\forge\
├── forge-backend.exe        # FastAPI server (bundled)
├── frontend/                # React UI (static files)
├── resources/               # Electron resources
└── FORGE.exe                # Desktop app launcher
```

User data and workspaces:
```
C:\Users\{Username}\AppData\Roaming\FORGE\
├── builder.db               # Job history, projects, settings
├── .forge_key               # Encryption key for secrets
└── workspaces/              # Generated code projects
    ├── project1_abc123/
    ├── project2_def456/
    └── ...
```

---

## 🔧 Configuring FORGE

### Environment Variables (Optional)
Create `.env` file in project root:

```bash
# LLM Configuration
MODE=LOCAL                    # LOCAL or CLOUD
LLM_PROVIDER=AUTO             # AUTO, LMSTUDIO, or OPENAI

# LM Studio (Local LLM)
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_MODEL=gpt-oss-20b

# OpenAI (Cloud LLM)
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini

# Custom Data Directory (Optional)
FORGE_DATA_DIR=C:\CustomPath\FORGEData
```

### Settings UI (Recommended)
Users can configure FORGE through the UI:
1. Click **⚙️ Settings** icon in left pane
2. Set **LM Studio URL** (for local LLM)
3. Set **OpenAI API Key** (for cloud LLM)
4. Settings are encrypted and stored in database

**Precedence:** Database settings → Environment variables → Defaults

---

## 🧪 Testing Before GitHub Push

### Test Checklist

1. **✅ Test with OpenAI API**
   - Set OpenAI API key in Settings
   - Create a simple project: "Build a CLI that prints Hello World"
   - Verify: Plan → Code → Test → Success
   - Note: Speed and cost

2. **✅ Test with Local LLM (LM Studio)**
   - Install [LM Studio](https://lmstudio.ai/)
   - Download a compatible model (e.g., Mistral 7B, Llama 3)
   - Start local server in LM Studio
   - Set provider to LMSTUDIO in FORGE
   - Create same test project
   - Compare: Speed vs quality vs OpenAI

3. **✅ Test File Upload**
   - Create a `.txt` or `.docx` spec file
   - Click **📁 Upload File** in Build Settings
   - Verify spec loads correctly
   - Create project from uploaded spec

4. **✅ Test Conversational Iteration**
   - Create a project
   - Select it from Projects list
   - Chat: "Add error handling"
   - Chat: "Add logging"
   - Verify context awareness

5. **✅ Test Export/Download**
   - Complete a successful build
   - Go to Artifacts tab
   - Click **📥 Download as ZIP**
   - Extract and verify files
   - Click **📂 Copy Workspace Path**
   - Verify path is correct

6. **✅ Test Windows Build**
   - Run `python build.py --all --clean`
   - Verify installer created in `launcher/dist/`
   - Install on test Windows machine
   - Verify app launches and works

---

## 📊 Performance Comparison: Local vs Cloud LLM

### OpenAI GPT-4 (Cloud)
✅ **Pros:**
- Fast response times (typically 2-10 seconds)
- High-quality code generation
- Reliable and consistent
- Handles complex specs well

❌ **Cons:**
- Costs money ($0.15-$0.60 per run typically)
- Requires internet connection
- API key management
- Usage limits

### LM Studio (Local)
✅ **Pros:**
- Completely free
- No internet required
- Unlimited usage
- Privacy (code stays local)

❌ **Cons:**
- Slower (10-60 seconds depending on hardware)
- Requires powerful GPU for best performance
- Quality varies by model
- Large models need 16GB+ VRAM

### Recommendation
- **Development/Testing:** Use local LLM to save costs
- **Production/Complex Projects:** Use OpenAI for quality
- **Privacy-Sensitive:** Stick with local LLM
- **Best of Both:** Switch between them based on task complexity!

---

## 🎯 Pre-GitHub Checklist

Before pushing to GitHub, verify:

- [ ] `.gitignore` excludes:
  - `node_modules/`
  - `__pycache__/`
  - `.env`
  - `build/`
  - `dist/`
  - `*.pyc`
  - Database files (`*.db`)
  
- [ ] `README.md` includes:
  - Project description
  - Installation instructions
  - Quick start guide
  - Screenshots
  
- [ ] All secrets removed from code
  - No API keys in files
  - No hardcoded passwords
  - Settings use environment variables
  
- [ ] Build process works
  - `python build.py --all --clean` succeeds
  - Installer runs on fresh Windows machine
  
- [ ] Core features tested
  - OpenAI integration works
  - LM Studio integration works
  - File upload works
  - Conversational iteration works
  - Export/download works

---

## 🚢 Deployment Options

### Option 1: Desktop App (Electron)
**Best for:** Individual users, local development
- Build with `python build.py --all --clean`
- Distribute `FORGE Setup X.X.X.exe`
- Users install and run locally
- All data stays on their machine

### Option 2: Web Deployment (Replit/Cloud)
**Best for:** Teams, cloud-based workflows
- Deploy backend to cloud (Replit, AWS, etc.)
- Host frontend on CDN/static hosting
- Users access via browser
- Workspaces stored server-side

### Option 3: Hybrid
**Best for:** Maximum flexibility
- Offer both desktop app and web version
- Let users choose based on needs
- Same codebase, different deployment

---

## 📞 Support

For issues or questions:
1. Check the logs in `%APPDATA%\FORGE\` 
2. Review Build Process logs in console
3. Test with simple spec first
4. Compare OpenAI vs Local LLM results

---

**FORGE — Where Concepts Become Systems** 🔥
