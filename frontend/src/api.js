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
