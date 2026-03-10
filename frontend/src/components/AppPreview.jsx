import React, { useState, useEffect, useRef } from 'react'

export default function AppPreview({ appPort, buildStatus }) {
  const iframeRef = useRef(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const appUrl = appPort ? `http://localhost:${appPort}` : null

  useEffect(() => {
    if (buildStatus === 'complete' && iframeRef.current && appUrl) {
      iframeRef.current.src = appUrl
    }
  }, [buildStatus, appUrl])

  if (!appUrl) {
    return (
      <div className="flex items-center justify-center h-full text-[#666] text-sm">
        <div className="text-center">
          <div className="text-4xl mb-3 opacity-30">🌐</div>
          <p>No app running</p>
          <p className="text-xs mt-1">Start a build to preview your app</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-1.5 bg-[#1C1C1C] border-b border-[#2B2B2B] text-xs">
        <span className="text-[#888]">{appUrl}</span>
        <button
          className="ml-auto px-2 py-0.5 text-[#888] hover:text-[#ccc] hover:bg-[#2B2B2B] rounded"
          onClick={() => {
            if (iframeRef.current) iframeRef.current.src = appUrl
          }}
        >
          ↻ Reload
        </button>
      </div>
      <div className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#1C1C1C] text-[#666] text-sm">
            Loading preview...
          </div>
        )}
        <iframe
          ref={iframeRef}
          src={appUrl}
          className="w-full h-full border-0 bg-white"
          onLoad={() => { setLoading(false); setError(false) }}
          onError={() => { setLoading(false); setError(true) }}
          title="App Preview"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        />
      </div>
    </div>
  )
}
