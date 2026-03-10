import React, { useState, useEffect } from 'react'

export default function StatusBar({ apiBase, buildStatus, project }) {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    const fetchHealth = () => {
      fetch(`${apiBase}/health`)
        .then(r => r.json())
        .then(setHealth)
        .catch(() => setHealth(null))
    }
    fetchHealth()
    const interval = setInterval(fetchHealth, 10000)
    return () => clearInterval(interval)
  }, [apiBase])

  const statusColor = {
    idle: 'text-[#666]',
    building: 'text-yellow-500',
    complete: 'text-green-500',
    failed: 'text-red-500',
  }[buildStatus || 'idle'] || 'text-[#666]'

  const statusLabel = {
    idle: 'Idle',
    building: 'Building...',
    complete: 'Build Complete',
    failed: 'Build Failed',
  }[buildStatus || 'idle'] || 'Idle'

  return (
    <div className="flex items-center justify-between px-4 py-1.5 bg-[#0e0e0e] border-t border-[#2B2B2B] text-xs">
      <div className="flex items-center gap-4">
        <span className="text-[#FF6E00] font-semibold">FORGE</span>
        {health ? (
          <>
            <span className="text-[#888]">
              Model: <span className="text-[#ccc]">{health.model || 'none'}</span>
            </span>
            <span className="text-[#888]">
              VRAM: <span className="text-[#ccc]">{health.total_vram_gb != null ? `${health.vram_free_gb}/${health.total_vram_gb} GB` : 'N/A'}</span>
            </span>
          </>
        ) : (
          <span className="text-red-400">Backend disconnected</span>
        )}
      </div>
      <div className="flex items-center gap-4">
        {project && <span className="text-[#888]">Project: <span className="text-[#ccc]">{project}</span></span>}
        <span className={statusColor}>{statusLabel}</span>
      </div>
    </div>
  )
}
