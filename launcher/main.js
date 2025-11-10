const { app, BrowserWindow } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const config = require('./forge-builder.config.json')

const isDev = !app.isPackaged
let backendProcess
let frontendProcess

function getBackendPath() {
  if (isDev) {
    return null // Use Python in dev mode
  }
  // In production, backend exe is in app resources folder
  const resourcePath = process.resourcesPath
  return path.join(resourcePath, 'forge-backend.exe')
}

function getFrontendPath() {
  if (isDev) {
    return null // Use dev server
  }
  // In production, frontend is bundled with the app (not in resources)
  // __dirname in packaged app points to app.asar/
  return path.join(__dirname, 'frontend', 'index.html')
}

function startBackend() {
  if (isDev) {
    // Development mode: run Python dev server
    const py = process.platform === 'win32' ? 'python' : 'python3'
    const cwd = path.join(__dirname, '..')
    backendProcess = spawn(
      py,
      ['-m', 'uvicorn', 'backend.app:app', '--host', '0.0.0.0', '--port', String(config.backendPort)],
      { cwd, shell: false }
    )
    backendProcess.stdout.on('data', d => console.log(`[backend] ${d}`))
    backendProcess.stderr.on('data', d => console.error(`[backend] ${d}`))
  } else {
    // Production mode: run frozen backend executable
    const backendExe = getBackendPath()
    console.log(`Starting backend from: ${backendExe}`)
    backendProcess = spawn(backendExe, [], { shell: false })
    backendProcess.stdout.on('data', d => console.log(`[backend] ${d}`))
    backendProcess.stderr.on('data', d => console.error(`[backend] ${d}`))
    backendProcess.on('error', err => {
      console.error('Failed to start backend:', err)
    })
  }
}

function startFrontend() {
  if (isDev) {
    // Development mode: run Vite dev server
    const cwd = path.join(__dirname, config.frontendPath)
    frontendProcess = spawn('npm', ['run', 'dev'], { cwd, shell: true })
    frontendProcess.stdout.on('data', d => console.log(`[frontend] ${d}`))
    frontendProcess.stderr.on('data', d => console.error(`[frontend] ${d}`))
  }
  // In production mode, we serve static files - no process needed
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1600,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  if (isDev) {
    // Development mode: load from dev server
    setTimeout(() => {
      mainWindow.loadURL(`http://localhost:${config.frontendPort}`)
    }, 3000)
  } else {
    // Production mode: load static files
    const frontendPath = getFrontendPath()
    console.log(`Loading frontend from: ${frontendPath}`)
    mainWindow.loadFile(frontendPath)
  }

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('Failed to load:', errorCode, errorDescription)
  })
}

app.whenReady().then(() => {
  startBackend()
  startFrontend()
  
  // Wait a bit for backend to start before creating window
  setTimeout(() => {
    createWindow()
  }, isDev ? 0 : 2000)

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('quit', () => {
  if (backendProcess) {
    backendProcess.kill()
  }
  if (frontendProcess) {
    frontendProcess.kill()
  }
})
