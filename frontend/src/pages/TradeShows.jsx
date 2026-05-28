import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { MapPin, ExternalLink, Calendar } from "lucide-react";

const CATEGORY = {
  textile:   { gradient: ["#7c3aed", "#6366f1"], label: "Textile"   },
  garment:   { gradient: ["#ea580c", "#f59e0b"], label: "Garment"   },
  fashion:   { gradient: ["#db2777", "#ec4899"], label: "Fashion"   },
  ecommerce: { gradient: ["#2563eb", "#06b6d4"], label: "E-Commerce" },
};

function fmt(d) {
  if (!d) return null;
  return new Date(d).toLocaleDateString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
  });
}

function monthAbbr(d) {
  if (!d) return "TBD";
  return new Date(d).toLocaleString("en-IN", { month: "short" }).toUpperCase();
}

function dayNum(d) {
  if (!d) return "—";
  return new Date(d).getDate();
}

function daysUntil(d) {
  if (!d) return null;
  const diff = Math.ceil((new Date(d) - new Date()) / (1000 * 60 * 60 * 24));
  if (diff < 0) return null;
  if (diff === 0) return "Today";
  if (diff <= 30) return `${diff}d away`;
  if (diff <= 90) return `${Math.ceil(diff / 7)}w away`;
  return `${Math.ceil(diff / 30)}mo away`;
}

function SkeletonRow() {
  return (
    <div className="glass-card" style={{ padding: 20, display: "flex", gap: 20, alignItems: "center" }}>
      <div className="shimmer rounded-xl" style={{ width: 64, height: 64, flexShrink: 0 }} />
      <div style={{ flex: 1 }}>
        <div className="shimmer rounded" style={{ height: 16, width: "45%", marginBottom: 10 }} />
        <div className="shimmer rounded" style={{ height: 12, width: "65%", marginBottom: 8 }} />
        <div className="shimmer rounded" style={{ height: 12, width: "80%" }} />
      </div>
      <div className="shimmer rounded-full" style={{ height: 28, width: 80 }} />
    </div>
  );
}

export default function TradeShows() {
  const [shows, setShows]     = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.tradeShows()
      .then(setShows)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-extrabold" style={{ color: "#0f172a", letterSpacing: "-0.02em" }}>
            Trade Shows
          </h2>
          <p className="text-sm font-medium mt-1" style={{ color: "#94a3b8" }}>
            {loading ? "Loading…" : `${shows.length} upcoming events tracked`}
          </p>
        </div>
        <div style={{
          display: "flex", alignItems: "center", gap: 8,
          padding: "8px 16px", borderRadius: 99,
          background: "rgba(124, 58, 237, 0.08)",
          border: "1px solid rgba(124, 58, 237, 0.15)",
        }}>
          <Calendar size={14} style={{ color: "#7c3aed" }} />
          <span style={{ fontSize: 12, fontWeight: 600, color: "#6d28d9" }}>2026 – 2027 calendar</span>
        </div>
      </div>

      {/* List */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {loading
          ? Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)
          : shows.length === 0
            ? (
              <div className="glass-card" style={{ padding: 60, textAlign: "center" }}>
                <Calendar size={36} style={{ color: "#e2e8f0", margin: "0 auto 12px" }} />
                <p style={{ color: "#94a3b8", fontSize: 14, fontStyle: "italic" }}>
                  No upcoming trade shows found.
                </p>
              </div>
            )
            : shows.map((t) => {
              const cat = CATEGORY[t.category] ?? { gradient: ["#94a3b8", "#64748b"], label: t.category };
              const [c1, c2] = cat.gradient;
              const until = daysUntil(t.start_date);

              return (
                <div
                  key={t.id}
                  className="glass-card"
                  style={{ padding: "18px 24px", display: "flex", gap: 20, alignItems: "flex-start" }}
                >
                  {/* Coloured date block */}
                  <div style={{
                    flexShrink: 0, width: 64, height: 64, borderRadius: 14,
                    background: `linear-gradient(135deg, ${c1}, ${c2})`,
                    display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center",
                    boxShadow: `0 4px 14px ${c1}40`,
                  }}>
                    <span style={{ fontSize: 9, fontWeight: 700, color: "rgba(255,255,255,0.8)", letterSpacing: "0.12em" }}>
                      {monthAbbr(t.start_date)}
                    </span>
                    <span style={{ fontSize: 24, fontWeight: 800, color: "#fff", lineHeight: 1, letterSpacing: "-0.02em" }}>
                      {dayNum(t.start_date)}
                    </span>
                  </div>

                  {/* Details */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 5, flexWrap: "wrap" }}>
                      <h3 style={{ fontSize: 15, fontWeight: 700, color: "#0f172a", letterSpacing: "-0.01em", margin: 0 }}>
                        {t.name}
                      </h3>
                      <span style={{
                        fontSize: 11, fontWeight: 600, padding: "2px 10px", borderRadius: 99,
                        background: `${c1}18`, color: c1, border: `1px solid ${c1}30`,
                        flexShrink: 0,
                      }}>
                        {cat.label}
                      </span>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#64748b", marginBottom: 6, flexWrap: "wrap" }}>
                      <MapPin size={11} style={{ flexShrink: 0 }} />
                      <span style={{ fontWeight: 500 }}>{t.city ?? "TBD"}</span>
                      {t.venue && <><span style={{ color: "#cbd5e1" }}>·</span><span>{t.venue}</span></>}
                      <span style={{ color: "#cbd5e1" }}>·</span>
                      <span style={{ color: "#94a3b8" }}>
                        {fmt(t.start_date)}
                        {t.end_date && t.end_date !== t.start_date ? ` – ${fmt(t.end_date)}` : ""}
                      </span>
                    </div>

                    {t.relevance_note && (
                      <p style={{ fontSize: 12, color: "#64748b", fontStyle: "italic", margin: 0 }}>
                        {t.relevance_note}
                      </p>
                    )}
                  </div>

                  {/* Right side: countdown + link */}
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 10, flexShrink: 0 }}>
                    {until && (
                      <span style={{
                        fontSize: 11, fontWeight: 700, padding: "4px 12px", borderRadius: 99,
                        background: `${c1}12`, color: c1, border: `1px solid ${c1}25`,
                        whiteSpace: "nowrap",
                      }}>
                        {until}
                      </span>
                    )}
                    {t.website && (
                      <a
                        href={t.website}
                        target="_blank"
                        rel="noreferrer"
                        style={{ color: "#94a3b8", transition: "color 0.2s" }}
                        onMouseEnter={e => e.currentTarget.style.color = "#6366f1"}
                        onMouseLeave={e => e.currentTarget.style.color = "#94a3b8"}
                      >
                        <ExternalLink size={14} />
                      </a>
                    )}
                  </div>
                </div>
              );
            })
        }
      </div>
    </div>
  );
}
