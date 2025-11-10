import React, { useState, useEffect } from 'react'
import { submitJob, setProvider, createProject, listProjects } from '../api'

export default function LeftPane({ onOpenSettings, onJobSubmitted, selectedProject, onSelectProject }) {
  const [project_name, setName] = useState('forge-mvp')
  const [spec, setSpec] = useState('Build a CLI that prints "FORGE" and a pytest that asserts output contains FORGE')
  const [provider, setProv] = useState('AUTO')
  const [submitting, setSubmitting] = useState(false)
  const [activity, setActivity] = useState([])
  const [projects, setProjects] = useState([])
  const [mode, setMode] = useState('new') // 'new' or 'existing'

  useEffect(() => {
    loadProjects()
  }, [])

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

  return (
    <div className="pane left">
      <div className="settings-header">
        <h2>FORGE</h2>
        <button className="settings-icon" onClick={onOpenSettings} title="Settings">
          ⚙️
        </button>
      </div>
      <p className="tagline">Where Concepts Become Systems</p>
      
      {/* Projects List */}
      {projects.length > 0 && (
        <div className="projects-panel" style={{ marginBottom: '20px' }}>
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
      
      {/* Build Form */}
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
      
      <h3>{mode === 'new' ? 'New Project' : 'Modify Project'}</h3>
      
      {mode === 'new' && (
        <>
          <label>Project Name</label>
          <input
            value={project_name}
            onChange={e => setName(e.target.value)}
            placeholder="Project name"
          />
        </>
      )}
      
      <label>{mode === 'new' ? 'Specification' : 'Modification Request'}</label>
      <textarea
        value={spec}
        onChange={e => setSpec(e.target.value)}
        rows={mode === 'new' ? 14 : 8}
        placeholder={mode === 'new' ? 'Describe what you want to build...' : 'Describe what you want to change...'}
      />
      
      <button onClick={run} disabled={submitting || (mode === 'existing' && !selectedProject)}>
        {submitting ? 'Submitting...' : mode === 'new' ? 'Create Project' : 'Apply Changes'}
      </button>
      
      <div className="toggle">
        <label>LLM Provider:</label>
        <select value={provider} onChange={e => setProvRemote(e.target.value)}>
          <option>AUTO</option>
          <option>LMSTUDIO</option>
          <option>OPENAI</option>
        </select>
      </div>
      
      <p className="hint">
        AUTO prefers LM Studio in LOCAL mode, OpenAI in CLOUD mode.
        OPENAI requires API key.
      </p>

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
    </div>
  )
}
