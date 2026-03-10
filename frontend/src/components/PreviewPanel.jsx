import React, { useState } from 'react'
import AppPreview from './AppPreview'
import FileDiffs from './FileDiffs'
import Terminal from './Terminal'

const TABS = [
  { id: 'preview', label: 'App Preview' },
  { id: 'diffs', label: 'File Diffs' },
  { id: 'terminal', label: 'Terminal' },
]

export default function PreviewPanel({ appPort, buildStatus, events }) {
  const [activeTab, setActiveTab] = useState('terminal')

  return (
    <div className="flex flex-col h-full bg-[#0e0e0e] border-l border-[#2B2B2B]">
      {/* Tab bar */}
      <div className="flex border-b border-[#2B2B2B]">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`px-4 py-2 text-xs font-medium transition-colors ${
              activeTab === tab.id
                ? 'text-[#FF6E00] border-b-2 border-[#FF6E00] bg-[#1C1C1C]'
                : 'text-[#888] hover:text-[#ccc] border-b-2 border-transparent'
            }`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'preview' && (
          <AppPreview appPort={appPort} buildStatus={buildStatus} />
        )}
        {activeTab === 'diffs' && (
          <FileDiffs events={(events || []).filter(e =>
            ['FILE_CHANGED', 'BUILD_ERROR', 'FIX_APPLIED'].includes(e.event)
          )} />
        )}
        {activeTab === 'terminal' && (
          <Terminal events={events || []} />
        )}
      </div>
    </div>
  )
}
