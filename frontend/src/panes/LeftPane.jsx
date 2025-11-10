import React, { useState } from 'react'
import { submitJob, setProvider } from '../api'

export default function LeftPane({ onOpenSettings, onJobSubmitted }) {
  const [project_name, setName] = useState('forge-mvp')
  const [spec, setSpec] = useState('Build a CLI that prints "FORGE" and a pytest that asserts output contains FORGE')
  const [provider, setProv] = useState('AUTO')
  const [submitting, setSubmitting] = useState(false)
  const [activity, setActivity] = useState([])

  async function run() {
    setSubmitting(true)
    const timestamp = new Date().toLocaleTimeString()
    try {
      const result = await submitJob({ project_name, spec })
      setActivity(prev => [...prev, {
        time: timestamp,
        message: `Submitted "${project_name}"`,
        type: 'success'
      }])
      if (onJobSubmitted && result.job_id) {
        onJobSubmitted({ id: result.job_id, project_name, status: 'queued' })
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
      
      <h3>New Build</h3>
      <label>Project Name</label>
      <input
        value={project_name}
        onChange={e => setName(e.target.value)}
        placeholder="Project name"
      />
      
      <label>Specification</label>
      <textarea
        value={spec}
        onChange={e => setSpec(e.target.value)}
        rows={14}
        placeholder="Describe what you want to build..."
      />
      
      <button onClick={run} disabled={submitting}>
        {submitting ? 'Submitting...' : 'Run Build'}
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
