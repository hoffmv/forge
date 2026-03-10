import React, { useRef, useEffect } from 'react'

export default function FileDiffs({ events }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  if (!events || events.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-[#666] text-sm">
        <div className="text-center">
          <div className="text-4xl mb-3 opacity-30">📝</div>
          <p>No file changes yet</p>
          <p className="text-xs mt-1">Changes will appear here during builds</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto p-2 gap-2">
      {events.map((evt, i) => (
        <DiffEntry key={i} event={evt} />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}

function DiffEntry({ event }) {
  const isError = event.event === 'BUILD_ERROR'
  const isFix = event.event === 'FIX_APPLIED'
  const isChange = event.event === 'FILE_CHANGED'

  let borderColor = 'border-[#2B2B2B]'
  let icon = '📄'
  let label = event.file || 'unknown'

  if (isError) {
    borderColor = 'border-red-500/40'
    icon = '❌'
    label = `Error (iteration ${event.iteration || '?'})`
  } else if (isFix) {
    borderColor = 'border-green-500/40'
    icon = '🔧'
    label = event.file || 'Fix applied'
  } else if (isChange) {
    borderColor = 'border-[#FF6E00]/40'
    icon = '✏️'
  }

  const time = event.timestamp
    ? new Date(event.timestamp).toLocaleTimeString()
    : ''

  return (
    <div className={`border ${borderColor} rounded bg-[#1C1C1C] p-2 text-xs`}>
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium text-[#ccc]">
          {icon} {label}
        </span>
        {time && <span className="text-[#666]">{time}</span>}
      </div>
      {event.diff && (
        <div className="text-[#888] font-mono whitespace-pre-wrap break-all">
          {event.diff}
        </div>
      )}
      {event.error && (
        <div className="text-red-400 font-mono whitespace-pre-wrap break-all mt-1">
          {event.error}
        </div>
      )}
      {event.summary && (
        <div className="text-green-400 font-mono whitespace-pre-wrap break-all mt-1">
          {event.summary}
        </div>
      )}
    </div>
  )
}
