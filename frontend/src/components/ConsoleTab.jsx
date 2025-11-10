import React from 'react'

export default function ConsoleTab({ selectedJob }) {
  if (!selectedJob) {
    return (
      <div className="tab-placeholder">
        <div className="preview-icon">💻</div>
        <h4>Console Output</h4>
        <p>Select a job to view its final output</p>
      </div>
    )
  }

  return (
    <div className="console-container">
      <div className="console-header">
        <h4>{selectedJob.project_name}</h4>
        <span className={`status-badge ${selectedJob.status}`}>{selectedJob.status}</span>
      </div>
      
      <div className="console-output">
        <pre>{JSON.stringify(selectedJob.report || {}, null, 2)}</pre>
      </div>
    </div>
  )
}
