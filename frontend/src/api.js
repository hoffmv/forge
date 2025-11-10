const API = (path) => `/api${path}`;

export async function submitJob(payload) {
  const r = await fetch(API('/jobs'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to submit job' }));
    throw new Error(error.detail || 'Failed to submit job');
  }
  return r.json();
}

export async function listJobs() {
  const r = await fetch(API('/jobs'));
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to list jobs' }));
    throw new Error(error.detail || 'Failed to list jobs');
  }
  return r.json();
}

export async function getJob(id) {
  const r = await fetch(API(`/jobs/${id}`));
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to get job' }));
    throw new Error(error.detail || 'Failed to get job');
  }
  return r.json();
}

export async function setProvider(provider) {
  const r = await fetch(API('/jobs/provider'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider })
  });
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to set provider' }));
    throw new Error(error.detail || 'Failed to set provider');
  }
  return r.json();
}

export async function getSettings() {
  const r = await fetch(API('/settings/current'));
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to load settings' }));
    throw new Error(error.detail || 'Failed to load settings');
  }
  return r.json();
}

export async function setLMStudioConfig(base_url) {
  const r = await fetch(API('/settings/lmstudio'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ base_url })
  });
  if (!r.ok) {
    const error = await r.json();
    throw new Error(error.detail || 'Failed to save LM Studio configuration');
  }
  return r.json();
}

export async function setOpenAIConfig(api_key) {
  const r = await fetch(API('/settings/openai'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key })
  });
  if (!r.ok) {
    const error = await r.json();
    throw new Error(error.detail || 'Failed to save OpenAI configuration');
  }
  return r.json();
}

export async function listWorkspaceFiles(jobId) {
  const r = await fetch(API(`/workspace/${jobId}/files`));
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to list workspace files' }));
    throw new Error(error.detail || 'Failed to list workspace files');
  }
  return r.json();
}

export async function readWorkspaceFile(jobId, filePath) {
  const r = await fetch(API(`/workspace/${jobId}/files/${filePath}`));
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to read file' }));
    throw new Error(error.detail || 'Failed to read file');
  }
  return r.json();
}

// Project management
export async function createProject(name, description = '') {
  const r = await fetch(API('/projects/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description })
  });
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to create project' }));
    throw new Error(error.detail || 'Failed to create project');
  }
  return r.json();
}

export async function listProjects() {
  const r = await fetch(API('/projects/'));
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to list projects' }));
    throw new Error(error.detail || 'Failed to list projects');
  }
  return r.json();
}

export async function getProject(projectId) {
  const r = await fetch(API(`/projects/${projectId}`));
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to get project' }));
    throw new Error(error.detail || 'Failed to get project');
  }
  return r.json();
}

export async function deleteProject(projectId) {
  const r = await fetch(API(`/projects/${projectId}`), { method: 'DELETE' });
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to delete project' }));
    throw new Error(error.detail || 'Failed to delete project');
  }
  return r.json();
}

export async function getMessages(projectId) {
  const r = await fetch(API(`/projects/${projectId}/messages`));
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to get messages' }));
    throw new Error(error.detail || 'Failed to get messages');
  }
  return r.json();
}

export async function addMessage(projectId, role, content, jobId = null) {
  const r = await fetch(API(`/projects/${projectId}/messages`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role, content, job_id: jobId })
  });
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to add message' }));
    throw new Error(error.detail || 'Failed to add message');
  }
  return r.json();
}

// File upload
export async function uploadSpecFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const r = await fetch(API('/upload/spec'), {
    method: 'POST',
    body: formData
  });
  
  if (!r.ok) {
    const error = await r.json().catch(() => ({ detail: 'Failed to upload file' }));
    throw new Error(error.detail || 'Failed to upload file');
  }
  
  return r.json();
}
