import React, { useState, useEffect } from 'react'
import FileExplorer from './components/FileExplorer'
import Editor from './components/Editor'
import PreviewPanel from './components/PreviewPanel'
import ProjectDashboard from './components/ProjectDashboard'
import StatusBar from './components/StatusBar'
import useWebSocket from './hooks/useWebSocket'
import useProject from './hooks/useProject'

const API_BASE = 'http://localhost:8000'

export default function App() {
  const {
    projects,
    currentProject,
    setCurrentProject,
    createProject,
    deleteProject,
    startBuild,
    fetchProjects,
  } = useProject(API_BASE)

  const { events, connected, clearEvents } = useWebSocket(currentProject, API_BASE)

  const [selectedFile, setSelectedFile] = useState(null)
  const [buildStatus, setBuildStatus] = useState('idle')
  const [buildStatuses, setBuildStatuses] = useState({})
  const [appPort, setAppPort] = useState(null)

  // Derive build status from WebSocket events
  useEffect(() => {
    if (events.length === 0) return
    const last = events[events.length - 1]
    let newStatus = null
    switch (last.event) {
      case 'BUILD_STARTED':
        newStatus = 'building'
        break
      case 'BUILD_COMPLETE':
        newStatus = 'complete'
        break
      case 'BUILD_FAILED':
        newStatus = 'failed'
        break
    }
    if (newStatus) {
      setBuildStatus(newStatus)
      if (currentProject) {
        setBuildStatuses(prev => ({ ...prev, [currentProject]: newStatus }))
      }
    }
  }, [events, currentProject])

  // Reset file selection when switching projects
  useEffect(() => {
    setSelectedFile(null)
    setBuildStatus('idle')
    clearEvents()
  }, [currentProject])

  const handleCreateAndBuild = async (name, prompt) => {
    await createProject(name)
    setCurrentProject(name)
    clearEvents()
    setBuildStatus('building')
    setBuildStatuses(prev => ({ ...prev, [name]: 'building' }))
    await startBuild(name, prompt)
  }

  const handleDeleteProject = async (name) => {
    await deleteProject(name)
    fetchProjects()
  }

  const handleBackToDashboard = () => {
    setCurrentProject(null)
    setSelectedFile(null)
  }

  // Show dashboard when no project is selected
  if (!currentProject) {
    return (
      <div className="flex flex-col h-screen bg-[#1C1C1C] text-[#f3f3f3]">
        <ProjectDashboard
          projects={projects}
          onSelectProject={setCurrentProject}
          onCreateAndBuild={handleCreateAndBuild}
          onDeleteProject={handleDeleteProject}
          buildStatuses={buildStatuses}
        />
        <StatusBar apiBase={API_BASE} buildStatus="idle" project={null} />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-[#1C1C1C] text-[#f3f3f3]">
      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — File Explorer */}
        <div className="w-64 flex-shrink-0">
          <div className="flex items-center px-3 py-1.5 bg-[#0e0e0e] border-b border-[#2B2B2B]">
            <button
              className="text-xs text-[#888] hover:text-[#FF6E00] transition-colors"
              onClick={handleBackToDashboard}
            >
              ← Dashboard
            </button>
          </div>
          <FileExplorer
            project={currentProject}
            selectedFile={selectedFile}
            onSelectFile={setSelectedFile}
            apiBase={API_BASE}
          />
        </div>

        {/* Center — Editor */}
        <div className="flex-1 min-w-0">
          <Editor
            project={currentProject}
            filePath={selectedFile}
            apiBase={API_BASE}
            isBuilding={buildStatus === 'building'}
          />
        </div>

        {/* Right — Preview Panel */}
        <div className="w-96 flex-shrink-0">
          <PreviewPanel
            appPort={appPort}
            buildStatus={buildStatus}
            events={events}
          />
        </div>
      </div>

      {/* Bottom — Status Bar */}
      <StatusBar
        apiBase={API_BASE}
        buildStatus={buildStatus}
        project={currentProject}
      />
    </div>
  )
}
