import React, { useState, useEffect } from 'react'

const FILE_ICONS = {
  py: '🐍', js: '📜', jsx: '⚛️', ts: '📘', tsx: '⚛️',
  html: '🌐', css: '🎨', json: '📋', md: '📝', txt: '📄',
  yml: '⚙️', yaml: '⚙️', toml: '⚙️', sql: '🗃️',
  default: '📄',
}

function getIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase()
  return FILE_ICONS[ext] || FILE_ICONS.default
}

function buildTree(files) {
  const tree = {}
  for (const file of files) {
    const parts = file.path.split('/')
    let node = tree
    for (let i = 0; i < parts.length - 1; i++) {
      if (!node[parts[i]]) node[parts[i]] = { __children: {} }
      node = node[parts[i]].__children
    }
    node[parts[parts.length - 1]] = { __file: file }
  }
  return tree
}

function TreeNode({ name, node, depth, selectedFile, onSelect, prefix }) {
  const [expanded, setExpanded] = useState(depth < 2)

  if (node.__file) {
    const file = node.__file
    const isSelected = selectedFile === file.path
    return (
      <div
        className={`flex items-center gap-2 px-2 py-1 cursor-pointer text-sm hover:bg-[#2B2B2B] ${isSelected ? 'bg-[#2B2B2B] border-l-2 border-[#FF6E00]' : 'border-l-2 border-transparent'}`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => onSelect(file.path)}
      >
        <span className="text-xs">{getIcon(name)}</span>
        <span className="truncate flex-1">{name}</span>
        <span className="text-xs text-[#666]">{formatSize(file.size)}</span>
      </div>
    )
  }

  const children = node.__children || node
  const entries = Object.entries(children).sort(([a, av], [b, bv]) => {
    const aIsDir = !av.__file
    const bIsDir = !bv.__file
    if (aIsDir !== bIsDir) return aIsDir ? -1 : 1
    return a.localeCompare(b)
  })

  return (
    <div>
      <div
        className="flex items-center gap-2 px-2 py-1 cursor-pointer text-sm hover:bg-[#2B2B2B] text-[#ccc]"
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-xs">{expanded ? '📂' : '📁'}</span>
        <span className="font-medium">{name}</span>
      </div>
      {expanded && entries.map(([childName, childNode]) => (
        <TreeNode
          key={childName}
          name={childName}
          node={childNode}
          depth={depth + 1}
          selectedFile={selectedFile}
          onSelect={onSelect}
          prefix={prefix ? `${prefix}/${childName}` : childName}
        />
      ))}
    </div>
  )
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}K`
  return `${(bytes / (1024 * 1024)).toFixed(1)}M`
}

export default function FileExplorer({ project, selectedFile, onSelectFile, apiBase }) {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!project) {
      setFiles([])
      return
    }
    setLoading(true)
    fetch(`${apiBase}/projects/${project}/files`)
      .then(r => r.json())
      .then(data => setFiles(data.files || []))
      .catch(() => setFiles([]))
      .finally(() => setLoading(false))
  }, [project, apiBase])

  const tree = buildTree(files)

  return (
    <div className="flex flex-col h-full bg-[#0e0e0e] border-r border-[#2B2B2B]">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#2B2B2B]">
        <h3 className="text-sm font-semibold text-[#FF6E00]">
          {project ? `📁 ${project}` : 'File Explorer'}
        </h3>
        <span className="text-xs text-[#666]">{files.length} files</span>
      </div>
      <div className="flex-1 overflow-y-auto py-1">
        {loading && <div className="px-4 py-8 text-center text-[#666] text-sm">Loading...</div>}
        {!loading && files.length === 0 && (
          <div className="px-4 py-8 text-center text-[#666] text-sm">
            {project ? 'No files yet' : 'Select a project'}
          </div>
        )}
        {!loading && Object.entries(tree).map(([name, node]) => (
          <TreeNode
            key={name}
            name={name}
            node={node}
            depth={0}
            selectedFile={selectedFile}
            onSelect={onSelectFile}
            prefix={name}
          />
        ))}
      </div>
    </div>
  )
}
