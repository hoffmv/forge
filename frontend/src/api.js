const API = (path) => `/api${path}`;

export async function submitJob(payload) {
  const r = await fetch(API('/jobs'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return r.json();
}

export async function listJobs() {
  const r = await fetch(API('/jobs'));
  return r.json();
}

export async function getJob(id) {
  const r = await fetch(API(`/jobs/${id}`));
  return r.json();
}

export async function setProvider(provider) {
  const r = await fetch(API('/jobs/provider'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider })
  });
  return r.json();
}
