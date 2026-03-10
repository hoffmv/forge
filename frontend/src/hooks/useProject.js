import { useState, useEffect, useCallback } from 'react'

export default function useProject(apiBase) {
  const [projects, setProjects] = useState([])
  const [currentProject, setCurrentProject] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchProjects = useCallback(() => {
    setLoading(true)
    fetch(`${apiBase}/projects`)
      .then(r => r.json())
      .then(data => {
        const list = data.projects || []
        setProjects(list)
        if (list.length > 0 && !currentProject) {
          setCurrentProject(list[0].name)
        }
      })
      .catch(() => setProjects([]))
      .finally(() => setLoading(false))
  }, [apiBase, currentProject])

  useEffect(() => {
    fetchProjects()
  }, [])

  const createProject = useCallback(async (name) => {
    const res = await fetch(`${apiBase}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    if (!res.ok) throw new Error('Failed to create project')
    const data = await res.json()
    setProjects(prev => [...prev, { name: data.name, path: data.path }])
    setCurrentProject(data.name)
    return data
  }, [apiBase])

  const deleteProject = useCallback(async (name) => {
    const res = await fetch(`${apiBase}/projects/${name}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Failed to delete project')
    setProjects(prev => prev.filter(p => p.name !== name))
    if (currentProject === name) {
      setCurrentProject(null)
    }
  }, [apiBase, currentProject])

  const startBuild = useCallback(async (projectName, taskDescription) => {
    const res = await fetch(`${apiBase}/agent/build`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project: projectName,
        task_description: taskDescription,
      }),
    })
    if (!res.ok) throw new Error('Failed to start build')
    return res.json()
  }, [apiBase])

  return {
    projects,
    currentProject,
    setCurrentProject,
    loading,
    fetchProjects,
    createProject,
    deleteProject,
    startBuild,
  }
}
