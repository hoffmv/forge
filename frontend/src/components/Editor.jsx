import React, { useState, useEffect } from 'react'
import MonacoEditor from '@monaco-editor/react'

const LANG_MAP = {
  py: 'python', js: 'javascript', jsx: 'javascript', ts: 'typescript', tsx: 'typescript',
  html: 'html', css: 'css', scss: 'scss', json: 'json', md: 'markdown',
  yml: 'yaml', yaml: 'yaml', toml: 'toml', sql: 'sql', sh: 'shell',
  rs: 'rust', go: 'go', java: 'java', c: 'c', cpp: 'cpp', cs: 'csharp',
  rb: 'ruby', php: 'php', xml: 'xml', txt: 'plaintext',
}

function detectLanguage(filepath) {
  if (!filepath) return 'plaintext'
  const ext = filepath.split('.').pop().toLowerCase()
  return LANG_MAP[ext] || 'plaintext'
}

export default function Editor({ project, filePath, apiBase, isBuilding }) {
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!project || !filePath) {
      setContent('')
      setError(null)
      return
    }

    setLoading(true)
    setError(null)
    fetch(`${apiBase}/projects/${project}/files/${filePath}`)
      .then(r => {
        if (!r.ok) throw new Error('Failed to load file')
        return r.json()
      })
      .then(data => setContent(data.content || ''))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [project, filePath, apiBase])

  if (!project || !filePath) {
    return (
      <div className="flex items-center justify-center h-full bg-[#1C1C1C]">
        <div className="text-center text-[#666]">
          <div className="text-5xl mb-4 opacity-30">📝</div>
          <h4 className="text-[#999] mb-2">No File Selected</h4>
          <p className="text-sm">Select a file from the explorer to view it here</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-[#1C1C1C]">
        <div className="text-[#666] text-sm">Loading {filePath}...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-[#1C1C1C]">
        <div className="text-red-400 text-sm">{error}</div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 bg-[#0e0e0e] border-b border-[#2B2B2B]">
        <span className="text-sm text-[#FF6E00] font-medium">{filePath}</span>
        {isBuilding && (
          <span className="text-xs text-yellow-500 bg-yellow-500/10 px-2 py-1 rounded">
            Read-only during build
          </span>
        )}
      </div>
      <div className="flex-1">
        <MonacoEditor
          height="100%"
          language={detectLanguage(filePath)}
          value={content}
          theme="vs-dark"
          options={{
            readOnly: isBuilding,
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            automaticLayout: true,
            padding: { top: 8 },
          }}
          onChange={(value) => {
            if (!isBuilding) setContent(value || '')
          }}
        />
      </div>
    </div>
  )
}
