import React, { useEffect, useRef } from 'react'

export default function BuildProcessTab({ selectedJob }) {
  const logsEndRef = useRef(null)

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [selectedJob?.logs])

  if (!selectedJob) {
    return (
      <div className="tab-placeholder">
        <div className="preview-icon">🔨</div>
        <h4>Build Process</h4>
        <p>Submit a build to see the process in real-time</p>
        <p className="hint-text">Watch FORGE plan, code, and test</p>
      </div>
    )
  }

  const logs = selectedJob.logs || []

  return (
    <div className="build-logs-container">
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
          
          {log.type === 'architect' && (
            <div className="log-architect">
              <div className="log-header">
                🏗️ AI Architect Review (Iteration {log.content.iteration})
              </div>
              <div className="architect-summary">
                <span className={`severity-badge ${log.content.severity}`}>
                  {log.content.severity}
                </span>
                <span className="architect-status">
                  {log.content.has_issues ? '⚠️ Issues Found' : '✅ Code Approved'}
                </span>
              </div>
              {log.content.summary && (
                <div className="architect-text">{log.content.summary}</div>
              )}
              {log.content.issues && log.content.issues.length > 0 && (
                <div className="architect-issues">
                  {log.content.issues.map((issue, idx) => (
                    <div key={idx} className="issue-item">
                      <div className="issue-header">
                        <span className={`issue-type ${issue.type}`}>{issue.type}</span>
                        <span className="issue-file">{issue.file}:{issue.line}</span>
                      </div>
                      <div className="issue-desc">{issue.description}</div>
                      <div className="issue-fix">💡 {issue.fix}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
      
      <div ref={logsEndRef} />
    </div>
  )
}
