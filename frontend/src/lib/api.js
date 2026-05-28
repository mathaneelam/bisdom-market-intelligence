const BASE = "http://localhost:8000";

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status} on ${path}`);
  return res.json();
}

export const api = {
  signalStats:   ()                         => get("/signals/stats"),
  signals:       (stream, limit = 50, offset = 0) => {
    const q = new URLSearchParams({ limit, offset });
    if (stream) q.set("stream", stream);
    return get(`/signals?${q}`);
  },
  todayBrief:    ()                         => get("/briefs/today"),
  briefs:        ()                         => get("/briefs"),
  competitors:   ()                         => get("/competitors"),
  tradeShows:    (upcomingOnly = true)      => get(`/trade-shows?upcoming_only=${upcomingOnly}`),
};
