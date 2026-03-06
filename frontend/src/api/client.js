const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(`${API_BASE}${path}`, opts);
  if (!res.ok) {
    let msg = `Erreur ${res.status}`;
    try { msg = (await res.json()).detail || msg; } catch (_) {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const searchListings = (params) => request('POST', '/search', params);
export const getPatterns = () => request('GET', '/patterns');
export const createPattern = (data) => request('POST', '/patterns', data);
export const deletePattern = (id) => request('DELETE', `/patterns/${id}`);
export const getVehicle = (brand, model) =>
  request('GET', `/vehicles?brand=${encodeURIComponent(brand)}&model=${encodeURIComponent(model)}`);
