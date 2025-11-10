import React, { useEffect, useState } from 'react'
import { listJobs, getJob } from '../api'

export default function CenterPane({ selectedJob, onSelectJob }) {
  const [jobs, setJobs] = useState([])

  useEffect(() => {
    const t = setInterval(async () => {
      const js = await listJobs()
      setJobs(js)
      if (selectedJob) {
        const updated = await getJob(selectedJob.id)
        onSelectJob(updated)
      }
    }, 1000)
    return () => clearInterval(t)
  }, [selectedJob])

  return (
    <div className="pane center">
      <h3>Jobs</h3>
      <ul className="joblist">
        {jobs.map(j => (
          <li
            key={j.id}
            onClick={() => onSelectJob(j)}
            className={j.status + (selectedJob?.id === j.id ? ' selected' : '')}
          >
            <b>{j.project_name}</b> <span className="status-badge">({j.status})</span>
          </li>
        ))}
      </ul>
      
      <div className="logs">
        <h4>Status Report</h4>
        <pre>{selectedJob ? JSON.stringify(selectedJob.report || {}, null, 2) : 'Select a job to view details'}</pre>
      </div>
    </div>
  )
}
