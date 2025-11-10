import React, { useState } from 'react'
import LeftPane from './panes/LeftPane'
import TabbedPane from './panes/TabbedPane'
import SettingsModal from './components/SettingsModal'

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [selectedJob, setSelectedJob] = useState(null)
  const [selectedProject, setSelectedProject] = useState(null)

  return (
    <>
      <div className="two-column-layout">
        <LeftPane 
          onOpenSettings={() => setSettingsOpen(true)} 
          onJobSubmitted={setSelectedJob}
          selectedProject={selectedProject}
          onSelectProject={setSelectedProject}
        />
        <TabbedPane 
          selectedJob={selectedJob} 
          onSelectJob={setSelectedJob}
        />
      </div>
      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  )
}
