import React, { useState, useEffect } from 'react'
import { listJobs, getJob } from '../api'
import BuildProcessTab from '../components/BuildProcessTab'
import JobsTab from '../components/JobsTab'
import ConsoleTab from '../components/ConsoleTab'
import ArtifactsTab from '../components/ArtifactsTab'
import HelpTab from '../components/HelpTab'
import PreviewTab from '../components/PreviewTab'

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
          className={`tab ${activeTab === 'preview' ? 'active' : ''}`}
          onClick={() => setActiveTab('preview')}
        >
          Preview
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
        <button 
          className={`tab ${activeTab === 'help' ? 'active' : ''}`}
          onClick={() => setActiveTab('help')}
        >
          📖 Help
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'build' && <BuildProcessTab selectedJob={selectedJob} />}
        {activeTab === 'preview' && <PreviewTab selectedJob={selectedJob} />}
        {activeTab === 'artifacts' && <ArtifactsTab selectedJob={selectedJob} />}
        {activeTab === 'jobs' && <JobsTab jobs={jobs} selectedJob={selectedJob} onSelectJob={onSelectJob} />}
        {activeTab === 'console' && <ConsoleTab selectedJob={selectedJob} />}
        {activeTab === 'help' && <HelpTab />}
      </div>
    </div>
  )
}
