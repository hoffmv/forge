import React, { useState, useEffect, useRef } from 'react'
import { submitJob, setProvider, createProject, listProjects, uploadSpecFile } from '../api'
import ChatTab from '../components/ChatTab'

export default function LeftPane({ onOpenSettings, onJobSubmitted, selectedProject, onSelectProject }) {
  const [project_name, setName] = useState('forge-mvp')
  const [spec, setSpec] = useState('Build a CLI that prints "FORGE" and a pytest that asserts output contains FORGE')
  const [provider, setProv] = useState('AUTO')
  const [submitting, setSubmitting] = useState(false)
  const [activity, setActivity] = useState([])
  const [projects, setProjects] = useState([])
  const [mode, setMode] = useState('new') // 'new' or 'existing'
  const [buildFormCollapsed, setBuildFormCollapsed] = useState(false)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    loadProjects()
  }, [])

  // Auto-collapse build form when a project is selected
  useEffect(() => {
    if (selectedProject) {
      setBuildFormCollapsed(true)
    }
  }, [selectedProject])

  async function loadProjects() {
    try {
      const data = await listProjects()
      setProjects(data.projects || [])
    } catch (err) {
      console.error('Failed to load projects:', err)
    }
  }

  async function run() {
    setSubmitting(true)
    const timestamp = new Date().toLocaleTimeString()
    try {
      let projectId = selectedProject?.id
      
      // If mode is 'new', create a new project first
      if (mode === 'new') {
        const project = await createProject(project_name, spec)
        projectId = project.id
        await loadProjects()
        if (onSelectProject) {
          onSelectProject(project)
        }
      }
      
      // Submit job with project_id
      const result = await submitJob({ 
        project_name: projectId ? `project_${projectId.slice(0, 8)}` : project_name, 
        spec,
        project_id: projectId,
        mode: mode === 'new' ? 'create' : 'modify'
      })
      
      setActivity(prev => [...prev, {
        time: timestamp,
        message: mode === 'new' ? `Created "${project_name}"` : `Updated project`,
        type: 'success'
      }])
      
      if (onJobSubmitted && result.job_id) {
        onJobSubmitted({ id: result.job_id, project_name, status: 'queued' })
      }
      
      // Clear spec after submission if modifying existing project
      if (mode === 'existing') {
        setSpec('')
      }
    } catch (err) {
      setActivity(prev => [...prev, {
        time: timestamp,
        message: `Failed: ${err.message}`,
        type: 'error'
      }])
    } finally {
      setSubmitting(false)
    }
  }

  async function setProvRemote(p) {
    setProv(p)
    await setProvider(p)
  }

  async function handleFileUpload(event) {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    try {
      const result = await uploadSpecFile(file)
      setSpec(result.text)
      setActivity(prev => [...prev, {
        time: new Date().toLocaleTimeString(),
        message: `Loaded "${file.name}" (${result.length} chars)`,
        type: 'success'
      }])
    } catch (err) {
      setActivity(prev => [...prev, {
        time: new Date().toLocaleTimeString(),
        message: `Upload failed: ${err.message}`,
        type: 'error'
      }])
    } finally {
      setUploading(false)
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <div className="pane left">
      <div className="settings-header">
        <h2>FORGE</h2>
        <button className="settings-icon" onClick={onOpenSettings} title="Settings">
          ⚙️
        </button>
      </div>
      <p className="tagline">Where Concepts Become Systems</p>
      
      {/* Projects List - Always visible */}
      {projects.length > 0 && (
        <div className="projects-panel" style={{ marginBottom: '15px' }}>
          <h3>Projects</h3>
          <div style={{ 
            maxHeight: '120px', 
            overflowY: 'auto',
            border: '1px solid #444',
            borderRadius: '6px',
            background: '#2B2B2B'
          }}>
            {projects.map(project => (
              <div 
                key={project.id}
                onClick={() => {
                  if (onSelectProject) {
                    onSelectProject(project)
                  }
                  setMode('existing')
                }}
                style={{
                  padding: '10px',
                  cursor: 'pointer',
                  background: selectedProject?.id === project.id ? '#FF6E00' : 'transparent',
                  color: selectedProject?.id === project.id ? '#fff' : '#ccc',
                  borderBottom: '1px solid #444',
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (selectedProject?.id !== project.id) {
                    e.target.style.background = '#333'
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedProject?.id !== project.id) {
                    e.target.style.background = 'transparent'
                  }
                }}
              >
                <div style={{ fontWeight: 'bold', fontSize: '13px' }}>{project.name}</div>
                <div style={{ fontSize: '11px', opacity: 0.7, marginTop: '2px' }}>
                  {new Date(project.updated * 1000).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Collapsible Build Form Section */}
      <div style={{ 
        marginBottom: '15px',
        border: '1px solid #444',
        borderRadius: '6px',
        overflow: 'hidden'
      }}>
        {/* Collapse/Expand Header */}
        <div 
          onClick={() => setBuildFormCollapsed(!buildFormCollapsed)}
          style={{
            padding: '12px 15px',
            background: '#2B2B2B',
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: buildFormCollapsed ? 'none' : '1px solid #444'
          }}
        >
          <h3 style={{ margin: 0, fontSize: '14px', color: '#FF6E00' }}>
            {buildFormCollapsed ? '⚡ Build Settings' : '🔧 Build Settings'}
          </h3>
          <span style={{ color: '#888', fontSize: '18px' }}>
            {buildFormCollapsed ? '▼' : '▲'}
          </span>
        </div>

        {/* Collapsible Content */}
        {!buildFormCollapsed && (
          <div style={{ padding: '15px', background: '#1a1a1a' }}>
            <div style={{ marginBottom: '12px', display: 'flex', gap: '8px' }}>
              <button
                onClick={() => {
                  setMode('new')
                  if (onSelectProject) {
                    onSelectProject(null)
                  }
                }}
                style={{
                  flex: 1,
                  padding: '8px',
                  background: mode === 'new' ? '#FF6E00' : '#444',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: 'bold'
                }}
              >
                New Project
              </button>
              <button
                onClick={() => setMode('existing')}
                disabled={!selectedProject}
                style={{
                  flex: 1,
                  padding: '8px',
                  background: mode === 'existing' ? '#FF6E00' : '#444',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: selectedProject ? 'pointer' : 'not-allowed',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  opacity: selectedProject ? 1 : 0.5
                }}
              >
                Modify Selected
              </button>
            </div>
            
            <h4 style={{ marginBottom: '8px', fontSize: '13px' }}>
              {mode === 'new' ? 'New Project' : 'Modify Project'}
            </h4>
            
            {mode === 'new' && (
              <>
                <label style={{ fontSize: '12px' }}>Project Name</label>
                <input
                  value={project_name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Project name"
                />
              </>
            )}
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <label style={{ fontSize: '12px' }}>
                {mode === 'new' ? 'Specification' : 'Modification Request'}
              </label>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                style={{
                  padding: '4px 10px',
                  background: '#444',
                  color: '#FF6E00',
                  border: '1px solid #FF6E00',
                  borderRadius: '4px',
                  fontSize: '11px',
                  cursor: uploading ? 'not-allowed' : 'pointer',
                  opacity: uploading ? 0.5 : 1,
                  fontWeight: 'bold'
                }}
              >
                {uploading ? '📤 Uploading...' : '📁 Upload File'}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.md,.docx"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
            </div>
            <textarea
              value={spec}
              onChange={e => setSpec(e.target.value)}
              rows={mode === 'new' ? 8 : 6}
              placeholder={mode === 'new' ? 'Describe what you want to build...\n\nOr upload a .txt, .md, or .docx file using the button above' : 'Describe what you want to change...'}
            />
            
            <button onClick={run} disabled={submitting || (mode === 'existing' && !selectedProject)}>
              {submitting ? 'Submitting...' : mode === 'new' ? 'Create Project' : 'Apply Changes'}
            </button>
            
            <div className="toggle" style={{ marginTop: '12px' }}>
              <label style={{ fontSize: '12px' }}>LLM Provider:</label>
              <select value={provider} onChange={e => setProvRemote(e.target.value)}>
                <option>AUTO</option>
                <option>LMSTUDIO</option>
                <option>OPENAI</option>
              </select>
            </div>
            
            <p className="hint" style={{ fontSize: '11px', marginTop: '8px' }}>
              AUTO prefers LM Studio in LOCAL mode, OpenAI in CLOUD mode.
            </p>
          </div>
        )}
      </div>

      {activity.length > 0 && (
        <div className="activity-feed">
          <h4>Activity</h4>
          <div className="activity-list">
            {activity.slice(-5).reverse().map((item, i) => (
              <div key={i} className={`activity-item ${item.type}`}>
                <span className="activity-time">{item.time}</span>
                <span className="activity-message">{item.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat Interface - Expanded when project is selected */}
      <div style={{ 
        flex: selectedProject ? 1 : 0,
        display: 'flex',
        flexDirection: 'column',
        minHeight: selectedProject ? '400px' : 'auto',
        border: selectedProject ? '2px solid #FF6E00' : '1px solid #444',
        borderRadius: '8px',
        overflow: 'hidden',
        transition: 'all 0.3s ease'
      }}>
        <div style={{
          padding: '12px 15px',
          background: selectedProject ? '#FF6E00' : '#2B2B2B',
          borderBottom: '1px solid rgba(0,0,0,0.2)',
          fontWeight: 'bold',
          fontSize: '13px',
          color: '#fff'
        }}>
          💬 Conversational Mode
        </div>
        
        {selectedProject ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <ChatTab 
              projectId={selectedProject.id} 
              onJobCreated={onJobSubmitted}
            />
          </div>
        ) : (
          <div style={{ 
            padding: '30px 20px', 
            textAlign: 'center', 
            color: '#888',
            fontSize: '13px'
          }}>
            <div style={{ fontSize: '32px', marginBottom: '12px' }}>💬</div>
            <div>Select a project above to start chatting with FORGE</div>
          </div>
        )}
      </div>
    </div>
  )
}
