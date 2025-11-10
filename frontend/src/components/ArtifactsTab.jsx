import React, { useState, useEffect } from 'react'
import { listWorkspaceFiles, readWorkspaceFile, downloadWorkspace, getWorkspacePath } from '../api'

export default function ArtifactsTab({ selectedJob }) {
  const [files, setFiles] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileContent, setFileContent] = useState(null)
  const [loading, setLoading] = useState(false)
  const [workspacePath, setWorkspacePath] = useState(null)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    if (!selectedJob || selectedJob.status !== 'succeeded') {
      setFiles([])
      setSelectedFile(null)
      setFileContent(null)
      setWorkspacePath(null)
      return
    }

    const fetchFiles = async () => {
      try {
        const result = await listWorkspaceFiles(selectedJob.id)
        setFiles(result.files || [])
        
        // Also fetch workspace path
        const pathInfo = await getWorkspacePath(selectedJob.id)
        setWorkspacePath(pathInfo)
      } catch (err) {
        console.error('Failed to list files:', err)
        setFiles([])
      }
    }

    fetchFiles()
  }, [selectedJob?.id, selectedJob?.status])

  const handleDownload = async () => {
    setDownloading(true)
    try {
      await downloadWorkspace(selectedJob.id)
    } catch (err) {
      alert(`Failed to download workspace: ${err.message}`)
    } finally {
      setDownloading(false)
    }
  }

  const handleCopyPath = () => {
    if (workspacePath?.workspace_path) {
      navigator.clipboard.writeText(workspacePath.workspace_path)
      alert(`Copied path to clipboard:\n${workspacePath.workspace_path}`)
    }
  }

  const handleFileClick = async (file) => {
    setSelectedFile(file)
    setLoading(true)
    try {
      const result = await readWorkspaceFile(selectedJob.id, file.path)
      setFileContent(result.content)
    } catch (err) {
      console.error('Failed to read file:', err)
      setFileContent(`Error reading file: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  if (!selectedJob) {
    return (
      <div className="tab-placeholder">
        <div className="preview-icon">📦</div>
        <h4>Generated Artifacts</h4>
        <p>Select a successful build to view generated code</p>
      </div>
    )
  }

  if (selectedJob.status !== 'succeeded') {
    return (
      <div className="tab-placeholder">
        <div className="preview-icon">⏳</div>
        <h4>No Artifacts Yet</h4>
        <p>This build hasn't completed successfully</p>
        <p className="hint-text">Status: {selectedJob.status}</p>
      </div>
    )
  }

  if (files.length === 0) {
    return (
      <div className="tab-placeholder">
        <div className="preview-icon">📭</div>
        <h4>No Files Found</h4>
        <p>This workspace appears to be empty</p>
      </div>
    )
  }

  return (
    <div className="artifacts-container">
      <div className="artifacts-sidebar">
        <div className="artifacts-header">
          <h4>Generated Files</h4>
          <span className="file-count">{files.length} files</span>
        </div>
        
        {/* Export Actions */}
        <div style={{ padding: '15px', borderBottom: '1px solid #2B2B2B', background: '#1a1a1a' }}>
          <button
            onClick={handleDownload}
            disabled={downloading}
            style={{
              width: '100%',
              padding: '10px',
              background: downloading ? '#444' : '#FF6E00',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 'bold',
              cursor: downloading ? 'not-allowed' : 'pointer',
              marginBottom: '8px',
              fontSize: '13px'
            }}
          >
            {downloading ? '⏳ Downloading...' : '📥 Download as ZIP'}
          </button>
          
          {workspacePath && (
            <button
              onClick={handleCopyPath}
              style={{
                width: '100%',
                padding: '10px',
                background: '#2B2B2B',
                color: '#FF6E00',
                border: '1px solid #FF6E00',
                borderRadius: '6px',
                fontWeight: 'bold',
                cursor: 'pointer',
                fontSize: '13px'
              }}
              title={workspacePath.workspace_path}
            >
              📂 Copy Workspace Path
            </button>
          )}
          
          {workspacePath && (
            <div style={{
              marginTop: '10px',
              padding: '8px',
              background: '#2B2B2B',
              borderRadius: '4px',
              fontSize: '11px',
              color: '#888',
              wordBreak: 'break-all'
            }}>
              <div style={{ color: '#FF6E00', fontWeight: 'bold', marginBottom: '4px' }}>
                Workspace Location:
              </div>
              {workspacePath.workspace_path}
            </div>
          )}
        </div>
        
        <ul className="file-tree">
          {files.map((file, i) => (
            <li
              key={i}
              className={`file-item ${selectedFile?.path === file.path ? 'selected' : ''}`}
              onClick={() => handleFileClick(file)}
            >
              <span className="file-icon">
                {file.path.endsWith('.py') ? '🐍' : 
                 file.path.endsWith('.js') ? '📜' :
                 file.path.endsWith('.json') ? '📋' :
                 file.path.endsWith('.md') ? '📝' : '📄'}
              </span>
              <span className="file-name">{file.path}</span>
              <span className="file-size">{formatBytes(file.size)}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="artifacts-viewer">
        {!selectedFile ? (
          <div className="viewer-placeholder">
            <div className="preview-icon">👈</div>
            <p>Select a file to view its contents</p>
          </div>
        ) : loading ? (
          <div className="viewer-placeholder">
            <div className="preview-icon">⏳</div>
            <p>Loading...</p>
          </div>
        ) : (
          <div className="file-viewer">
            <div className="viewer-header">
              <span className="viewer-title">{selectedFile.path}</span>
              <span className="viewer-size">{formatBytes(selectedFile.size)}</span>
            </div>
            <pre className="code-content">{fileContent}</pre>
          </div>
        )}
      </div>
    </div>
  )
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
