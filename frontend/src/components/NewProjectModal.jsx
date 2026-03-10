import React, { useState } from 'react'

export default function NewProjectModal({ isOpen, onClose, onCreate }) {
  const [name, setName] = useState('')
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!prompt.trim()) return

    setLoading(true)
    setError(null)
    try {
      const projectName = name.trim() || prompt.trim().slice(0, 30).replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase()
      await onCreate(projectName, prompt.trim())
      setName('')
      setPrompt('')
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-[#1C1C1C] border border-[#2B2B2B] rounded-lg w-full max-w-lg p-6 shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold text-[#FF6E00] mb-4">New Project</h2>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-xs text-[#888] mb-1">Project Name (optional)</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="my-project"
              className="w-full px-3 py-2 bg-[#0e0e0e] border border-[#2B2B2B] rounded text-sm text-[#f3f3f3] placeholder-[#666] focus:outline-none focus:border-[#FF6E00]"
            />
          </div>

          <div className="mb-4">
            <label className="block text-xs text-[#888] mb-1">What should Forge build?</label>
            <textarea
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              placeholder="Describe the project you want to build..."
              rows={5}
              className="w-full px-3 py-2 bg-[#0e0e0e] border border-[#2B2B2B] rounded text-sm text-[#f3f3f3] placeholder-[#666] focus:outline-none focus:border-[#FF6E00] resize-none"
              autoFocus
            />
          </div>

          {error && (
            <div className="mb-4 text-sm text-red-400 bg-red-400/10 px-3 py-2 rounded">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-[#888] hover:text-[#ccc] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!prompt.trim() || loading}
              className="px-4 py-2 text-sm font-medium bg-[#FF6E00] text-white rounded hover:bg-[#e06200] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Creating...' : 'Create & Build'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
