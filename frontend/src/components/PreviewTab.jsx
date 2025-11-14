import React, { useState, useEffect } from 'react'

function getAPIUrl(path) {
  if (window.location.protocol === 'file:') {
    return `http://localhost:8000${path}`
  }
  return `/api${path}`
}

export default function PreviewTab({ selectedJob }) {
  const [previewUrl, setPreviewUrl] = useState(null)
  const [previewMode, setPreviewMode] = useState('readme')
  const [readmeContent, setReadmeContent] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!selectedJob || selectedJob.status !== 'succeeded') {
      setPreviewUrl(null)
      setReadmeContent('')
      return
    }

    const fetchPreview = async () => {
      try {
        const res = await fetch(getAPIUrl(`/workspace/${selectedJob.id}/preview`))
        const data = await res.json()
        
        if (data.preview_url) {
          setPreviewUrl(data.preview_url)
          setPreviewMode('web')
        } else if (data.readme) {
          setReadmeContent(data.readme)
          setPreviewMode('readme')
        } else {
          setError('No preview available for this project type')
        }
      } catch (err) {
        setError('Failed to load preview')
      }
    }

    fetchPreview()
  }, [selectedJob])

  if (!selectedJob) {
    return (
      <div className="preview-empty">
        <div className="empty-state">
          <h3>No Project Selected</h3>
          <p>Select or create a project to see preview</p>
        </div>
      </div>
    )
  }

  if (selectedJob.status !== 'succeeded') {
    return (
      <div className="preview-empty">
        <div className="empty-state">
          <h3>Preview Unavailable</h3>
          <p>Build must complete successfully to show preview</p>
          <p className="status-hint">Current status: <span className={`status-${selectedJob.status}`}>{selectedJob.status}</span></p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="preview-empty">
        <div className="empty-state">
          <h3>⚠️ {error}</h3>
          <p>This project may be a CLI tool or library without a web interface</p>
          <p>Check the <strong>Artifacts</strong> tab to view and download the code</p>
        </div>
      </div>
    )
  }

  return (
    <div className="preview-container">
      <div className="preview-header">
        <h3>Preview</h3>
        {previewUrl && (
          <a href={previewUrl} target="_blank" rel="noopener noreferrer" className="btn-secondary">
            Open in New Tab ↗
          </a>
        )}
      </div>

      <div className="preview-content">
        {previewMode === 'web' && previewUrl ? (
          <iframe
            src={previewUrl}
            title="Project Preview"
            className="preview-iframe"
            sandbox="allow-scripts allow-same-origin allow-forms"
          />
        ) : (
          <div className="preview-readme">
            <div className="readme-header">
              <h4>📄 README.md</h4>
              <p className="hint">This project doesn't have a web interface. Here's how to use it:</p>
            </div>
            <pre className="readme-content">{readmeContent || 'No README available'}</pre>
          </div>
        )}
      </div>
    </div>
  )
}
