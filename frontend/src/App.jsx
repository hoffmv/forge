import React, { useState } from 'react'
import LeftPane from './panes/LeftPane'
import CenterPane from './panes/CenterPane'
import RightPane from './panes/RightPane'
import SettingsModal from './components/SettingsModal'

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false)

  return (
    <>
      <div className="grid">
        <LeftPane onOpenSettings={() => setSettingsOpen(true)} />
        <CenterPane />
        <RightPane />
      </div>
      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  )
}
