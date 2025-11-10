import React, { useState, useEffect } from 'react'
import { getSettings, setLMStudioConfig, setOpenAIConfig } from '../api'

export default function SettingsModal({ isOpen, onClose }) {
  const [lmstudioUrl, setLmstudioUrl] = useState('')
  const [openaiKey, setOpenaiKey] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    if (isOpen) {
      loadSettings()
    }
  }, [isOpen])

  async function loadSettings() {
    try {
      const settings = await getSettings()
      setLmstudioUrl(settings.lmstudio_url || '')
      setOpenaiKey('')
      setMessage(null)
    } catch (err) {
      console.error('Failed to load settings:', err)
      setMessage({ type: 'error', text: `Failed to load settings: ${err.message}` })
    }
  }

  async function handleSave() {
    setSaving(true)
    setMessage(null)
    
    try {
      // Validate and save LM Studio URL if provided
      if (lmstudioUrl && lmstudioUrl.trim() !== '') {
        await setLMStudioConfig(lmstudioUrl.trim())
      }
      
      // Validate and save OpenAI API key if provided
      if (openaiKey && openaiKey.trim() !== '') {
        await setOpenAIConfig(openaiKey.trim())
      }
      
      // Only show success if we actually saved something
      if ((lmstudioUrl && lmstudioUrl.trim()) || (openaiKey && openaiKey.trim())) {
        setMessage({ type: 'success', text: 'Settings saved successfully!' })
        setTimeout(() => {
          onClose()
        }, 1500)
      } else {
        setMessage({ type: 'error', text: 'Please provide at least one setting to save' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Failed to save settings' })
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Settings</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          <div className="setting-group">
            <label>LM Studio Endpoint URL</label>
            <input
              type="text"
              value={lmstudioUrl}
              onChange={e => setLmstudioUrl(e.target.value)}
              placeholder="http://localhost:1234/v1"
            />
            <p className="setting-hint">
              URL of your local LM Studio server (e.g., http://localhost:1234/v1)
            </p>
          </div>

          <div className="setting-group">
            <label>OpenAI API Key</label>
            <input
              type="password"
              value={openaiKey}
              onChange={e => setOpenaiKey(e.target.value)}
              placeholder="sk-..."
            />
            <p className="setting-hint">
              Your OpenAI API key (starts with sk-). Will be encrypted and stored securely.
            </p>
          </div>

          {message && (
            <div className={`message ${message.type}`}>
              {message.text}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
