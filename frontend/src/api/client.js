const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

async function request(method, path, body, token) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (token) opts.headers['Authorization'] = `Bearer ${token}`;
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(`${API_BASE}${path}`, opts);
  if (!res.ok) {
    let msg = `Erreur ${res.status}`;
    try { msg = (await res.json()).detail || msg; } catch (_) {}
    const err = new Error(msg);
    err.status = res.status;
    throw err;
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

export const getLikes         = (token)   => request('GET', '/likes', undefined, token);
export const getLikedListings = ()         => request('GET', '/likes/listings');
export const addLike          = (id, token) => request('POST',   `/listings/${id}/like`, undefined, token);
export const removeLike       = (id, token) => request('DELETE',  `/listings/${id}/like`, undefined, token);

export const register    = (email, password) => request('POST', '/auth/register', { email, password });
export const verifyEmail = (token) => request('POST', '/auth/verify-email', { token });
export const loginApi    = (email, password) => request('POST', '/auth/login', { email, password });
export const getMe       = (token) => request('GET', '/auth/me', undefined, token);
export const getSavedSearches = (token) => request('GET', '/users/me/searches', undefined, token);

export const analyzeListingAI = (listingId) => request('POST', `/listings/${listingId}/analyze`);

export const getAiQuota = () => request('GET', '/ai/quota');

export const analyzeSearch = (searchHistoryId) => request('POST', `/search/${searchHistoryId}/analyze`);

export const getSearchHistory   = ()    => request('GET',    '/history/searches');
export const getViewedListings  = ()    => request('GET',    '/history/listings');
export const markListingViewed  = (id)  => request('POST',   `/history/listings/${id}`);
export const clearSearchHistory = ()    => request('DELETE', '/history/searches');
export const clearViewedHistory = ()    => request('DELETE', '/history/listings');
