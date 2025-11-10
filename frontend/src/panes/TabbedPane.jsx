import React, { useState, useEffect } from 'react'
import { listJobs, getJob } from '../api'
import BuildProcessTab from '../components/BuildProcessTab'
import JobsTab from '../components/JobsTab'
import ConsoleTab from '../components/ConsoleTab'
import ArtifactsTab from '../components/ArtifactsTab'

export default function TabbedPane({ selectedJob, onSelectJob }) {
  const [activeTab, setActiveTab] = useState('build')
  const [jobs, setJobs] = useState([])

  useEffect(() => {
    const interval = setInterval(async () => {
      const js = await listJobs()
      setJobs(js)
      if (selectedJob) {
        const updated = await getJob(selectedJob.id)
        onSelectJob(updated)
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [selectedJob])

  return (
    <div className="tabbed-pane">
      <div className="tabs-header">
        <button 
          className={`tab ${activeTab === 'build' ? 'active' : ''}`}
          onClick={() => setActiveTab('build')}
        >
          Build Process
        </button>
        <button 
          className={`tab ${activeTab === 'artifacts' ? 'active' : ''}`}
          onClick={() => setActiveTab('artifacts')}
        >
          Artifacts
        </button>
        <button 
          className={`tab ${activeTab === 'jobs' ? 'active' : ''}`}
          onClick={() => setActiveTab('jobs')}
        >
          Jobs
        </button>
        <button 
          className={`tab ${activeTab === 'console' ? 'active' : ''}`}
          onClick={() => setActiveTab('console')}
        >
          Console
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'build' && <BuildProcessTab selectedJob={selectedJob} />}
        {activeTab === 'artifacts' && <ArtifactsTab selectedJob={selectedJob} />}
        {activeTab === 'jobs' && <JobsTab jobs={jobs} selectedJob={selectedJob} onSelectJob={onSelectJob} />}
        {activeTab === 'console' && <ConsoleTab selectedJob={selectedJob} />}
      </div>
    </div>
  )
}
