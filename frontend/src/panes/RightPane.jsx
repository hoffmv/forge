import React, { useEffect, useRef } from 'react'

export default function RightPane({ selectedJob }) {
  const logsEndRef = useRef(null)

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [selectedJob?.logs])

  if (!selectedJob) {
    return (
      <div className="pane right">
        <h3>Preview</h3>
        <div className="preview-placeholder">
          <div className="preview-icon">🔨</div>
          <h4>Build Process</h4>
          <p>Select a job to see the build process</p>
          <p className="hint-text">Watch FORGE plan, code, and test in real-time</p>
        </div>
      </div>
    )
  }

  const logs = selectedJob.logs || []

  return (
    <div className="pane right">
      <h3>Build Process</h3>
      <div className="build-logs">
        {logs.length === 0 && selectedJob.status === 'queued' && (
          <div className="log-entry status">
            <span className="log-icon">⏳</span>
            <span className="log-text">Waiting to start...</span>
          </div>
        )}
        
        {logs.map((log, i) => (
          <div key={i} className={`log-entry ${log.type}`}>
            {log.type === 'status' && (
              <div className="log-status">{log.content}</div>
            )}
            
            {log.type === 'plan' && (
              <div className="log-plan">
                <div className="log-header">📋 Plan</div>
                <pre className="log-code">{log.content}</pre>
              </div>
            )}
            
            {log.type === 'file' && (
              <div className="log-file">
                <div className="log-header">📄 {log.content.path}</div>
                <pre className="log-code">{log.content.content}</pre>
              </div>
            )}
            
            {log.type === 'test' && (
              <div className="log-test">
                <div className="log-header">
                  {log.content.passed ? '✅' : '❌'} Test Results (Attempt {log.content.iteration})
                </div>
                <pre className="log-code">
                  {log.content.output.stdout || ''}
                  {log.content.output.stderr && (
                    <span className="test-error">{log.content.output.stderr}</span>
                  )}
                </pre>
              </div>
            )}
          </div>
        ))}
        
        <div ref={logsEndRef} />
      </div>
    </div>
  )
}
