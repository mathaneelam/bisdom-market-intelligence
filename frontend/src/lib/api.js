const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status} on ${path}`);
  return res.json();
}

async function patch(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status} on ${path}`);
  return res.json();
}

export const api = {
  signalStats:   ()                         => get("/signals/stats"),
  signals:       (stream, limit = 50, offset = 0, source = null) => {
    const q = new URLSearchParams({ limit, offset });
    if (stream) q.set("stream", stream);
    if (source) q.set("source", source);
    return get(`/signals?${q}`);
  },
  sources:       ()                         => get("/signals/sources"),
  todayBrief:    ()                         => get("/briefs/today"),
  briefs:        ()                         => get("/briefs"),
  competitors:   ()                         => get("/competitors"),
  tradeShows:    (upcomingOnly = true)      => get(`/trade-shows?upcoming_only=${upcomingOnly}`),
  topPatterns:   (limit = 5)               => get(`/patterns/top?limit=${limit}`),
  patterns:      ()                        => get("/patterns"),
  patternSignals:(id)                      => get(`/patterns/${id}/signals`),
  contentPieces: (filters = {}, limit = 50, offset = 0) => {
    const q = new URLSearchParams({ limit, offset });
    for (const [k, v] of Object.entries(filters)) if (v) q.set(k, v);
    return get(`/content-pieces?${q}`);
  },
  contentPiece:       (id)         => get(`/content-pieces/${id}`),
  updateContentPiece: (id, body)   => patch(`/content-pieces/${id}`, body),
  savedItems:         (type = null)=> {
    const q = new URLSearchParams();
    if (type) q.set("item_type", type);
    return get(`/saved-items?${q}`);
  },
  saveItem:           (body)       => {
    return fetch(`${BASE}/saved-items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(res => res.json());
  },
  deleteSavedItem:    (id)         => {
    return fetch(`${BASE}/saved-items/${id}`, { method: "DELETE" }).then(res => res.json());
  },
};
