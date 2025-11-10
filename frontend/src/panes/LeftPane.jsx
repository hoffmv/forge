import React, { useState } from 'react'
import { submitJob, setProvider } from '../api'

export default function LeftPane({ onOpenSettings }) {
  const [project_name, setName] = useState('forge-mvp')
  const [spec, setSpec] = useState('Build a CLI that prints "FORGE" and a pytest that asserts output contains FORGE')
  const [provider, setProv] = useState('AUTO')
  const [submitting, setSubmitting] = useState(false)

  async function run() {
    setSubmitting(true)
    try {
      await submitJob({ project_name, spec })
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
    </div>
  )
}
