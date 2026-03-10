import React, { useState } from 'react'
import NewProjectModal from './NewProjectModal'

const STATUS_COLORS = {
  building: { bg: 'bg-yellow-500/15', text: 'text-yellow-500', label: 'Building' },
  failed: { bg: 'bg-red-500/15', text: 'text-red-500', label: 'Error' },
  complete: { bg: 'bg-green-500/15', text: 'text-green-500', label: 'Clean' },
  idle: { bg: 'bg-[#2B2B2B]', text: 'text-[#888]', label: 'Idle' },
}

export default function ProjectDashboard({
  projects,
  onSelectProject,
  onCreateAndBuild,
  onDeleteProject,
  buildStatuses,
}) {
  const [modalOpen, setModalOpen] = useState(false)

  const handleCreate = async (name, prompt) => {
    await onCreateAndBuild(name, prompt)
  }

  return (
    <div className="flex flex-col h-full bg-[#1C1C1C]">
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-6 border-b border-[#2B2B2B]">
        <div>
          <h1 className="text-2xl font-bold text-[#FF6E00]">FORGE</h1>
          <p className="text-sm text-[#888] mt-1">Where Concepts Become Systems</p>
        </div>
        <button
          className="px-4 py-2 text-sm font-medium bg-[#FF6E00] text-white rounded hover:bg-[#e06200] transition-colors"
          onClick={() => setModalOpen(true)}
        >
          + New Project
        </button>
      </div>

      {/* Project grid */}
      <div className="flex-1 overflow-y-auto p-8">
        {projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-6xl mb-4 opacity-20">🔥</div>
            <h3 className="text-lg text-[#999] mb-2">No Projects Yet</h3>
            <p className="text-sm text-[#666] mb-6 max-w-md">
              Create your first project and describe what you want to build. Forge will handle the rest.
            </p>
            <button
              className="px-6 py-3 text-sm font-medium bg-[#FF6E00] text-white rounded-lg hover:bg-[#e06200] transition-colors"
              onClick={() => setModalOpen(true)}
            >
              Create First Project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map(p => {
              const status = (buildStatuses || {})[p.name] || 'idle'
              const colors = STATUS_COLORS[status] || STATUS_COLORS.idle
              return (
                <div
                  key={p.name}
                  className="bg-[#0e0e0e] border border-[#2B2B2B] rounded-lg p-4 cursor-pointer hover:border-[#FF6E00]/50 transition-colors group"
                  onClick={() => onSelectProject(p.name)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-sm font-semibold text-[#ccc] group-hover:text-[#FF6E00] transition-colors truncate flex-1">
                      {p.name}
                    </h3>
                    <span className={`text-xs px-2 py-0.5 rounded ${colors.bg} ${colors.text}`}>
                      {colors.label}
                    </span>
                  </div>
                  <div className="text-xs text-[#666]">
                    {p.file_count != null ? `${p.file_count} files` : 'Project'}
                  </div>
                  <div className="flex items-center justify-end mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      className="text-xs text-red-400 hover:text-red-300"
                      onClick={(e) => { e.stopPropagation(); onDeleteProject(p.name) }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <NewProjectModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreate={handleCreate}
      />
    </div>
  )
}
