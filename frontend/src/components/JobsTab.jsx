import React from 'react'

export default function JobsTab({ jobs, selectedJob, onSelectJob }) {
  if (jobs.length === 0) {
    return (
      <div className="tab-placeholder">
        <div className="preview-icon">📋</div>
        <h4>No Jobs Yet</h4>
        <p>Submit your first build to get started</p>
      </div>
    )
  }

  return (
    <div className="jobs-list-container">
      <ul className="joblist">
        {jobs.map(j => (
          <li
            key={j.id}
            onClick={() => onSelectJob(j)}
            className={j.status + (selectedJob?.id === j.id ? ' selected' : '')}
          >
            <div className="job-header">
              <b>{j.project_name}</b>
              <span className={`status-badge ${j.status}`}>{j.status}</span>
            </div>
            <div className="job-time">
              {new Date(j.created * 1000).toLocaleString()}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
