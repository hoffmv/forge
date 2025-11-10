import React, { useState } from 'react'
import LeftPane from './panes/LeftPane'
import CenterPane from './panes/CenterPane'
import RightPane from './panes/RightPane'
import SettingsModal from './components/SettingsModal'

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [selectedJob, setSelectedJob] = useState(null)

  return (
    <>
      <div className="grid">
        <LeftPane onOpenSettings={() => setSettingsOpen(true)} />
        <CenterPane selectedJob={selectedJob} onSelectJob={setSelectedJob} />
        <RightPane selectedJob={selectedJob} />
      </div>
      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  )
}
