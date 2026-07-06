import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { MapPin, ExternalLink, Calendar } from "lucide-react";
import SaveButton from "../components/SaveButton";

const CATEGORY = {
  textile:   { gradient: ["#1889F6", "#0A4FC4"], label: "Textile"    },
  garment:   { gradient: ["#F97316", "#F59E0B"], label: "Garment"    },
  fashion:   { gradient: ["#EF4444", "#F97316"], label: "Fashion"    },
  ecommerce: { gradient: ["#22C55E", "#1889F6"], label: "E-Commerce" },
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
  if (diff < 0)  return null;
  if (diff === 0) return "Today";
  if (diff <= 30) return `${diff}d away`;
  if (diff <= 90) return `${Math.ceil(diff / 7)}w away`;
  return `${Math.ceil(diff / 30)}mo away`;
}

function SkeletonRow() {
  return (
    <div className="glass-card" style={{ padding: "18px 24px", display: "flex", gap: 20, alignItems: "center" }}>
      <div className="shimmer" style={{ width: 64, height: 64, borderRadius: 14, flexShrink: 0 }} />
      <div style={{ flex: 1 }}>
        <div className="shimmer" style={{ height: 14, width: "45%", marginBottom: 10 }} />
        <div className="shimmer" style={{ height: 11, width: "65%", marginBottom: 8 }} />
        <div className="shimmer" style={{ height: 11, width: "80%" }} />
      </div>
      <div className="shimmer" style={{ height: 26, width: 80, borderRadius: 99 }} />
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
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 32 }}>
        <div>
          <p className="section-label">Calendar</p>
          <h2 style={{
            fontFamily: "'Montserrat Alternates', sans-serif",
            fontSize: 28, fontWeight: 800,
            color: "var(--text)", letterSpacing: "-1.2px",
            margin: "0 0 6px",
          }}>
            Trade Shows
          </h2>
          <p style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 500, margin: 0 }}>
            {loading ? "Loading…" : `${shows.length} upcoming events tracked`}
          </p>
        </div>
        <div style={{
          display: "flex", alignItems: "center", gap: 7,
          padding: "7px 16px", borderRadius: 99,
          background: "var(--blue-tint)",
          border: "1px solid rgba(24,137,246,.18)",
        }}>
          <Calendar size={13} style={{ color: "var(--blue)" }} />
          <span style={{ fontSize: 11, fontWeight: 700, color: "var(--blue)", textTransform: "uppercase", letterSpacing: ".8px" }}>
            2026–2027
          </span>
        </div>
      </div>

      {/* List */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {loading
          ? Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)
          : shows.length === 0
            ? (
              <div className="glass-card" style={{ padding: 60, textAlign: "center" }}>
                <Calendar size={36} style={{ color: "var(--text-dim)", margin: "0 auto 12px", display: "block" }} />
                <p style={{ color: "var(--text-dim)", fontSize: 13, fontStyle: "italic", margin: 0 }}>
                  No upcoming trade shows found.
                </p>
              </div>
            )
            : shows.map(t => {
              const cat = CATEGORY[t.category] ?? { gradient: ["#1889F6", "#0A4FC4"], label: t.category };
              const [c1, c2] = cat.gradient;
              const until = daysUntil(t.start_date);

              return (
                <div
                  key={t.id}
                  className="glass-card"
                  style={{ padding: "18px 24px", display: "flex", gap: 20, alignItems: "flex-start" }}
                >
                  {/* Date block */}
                  <div style={{
                    flexShrink: 0, width: 64, height: 64, borderRadius: 14,
                    background: `linear-gradient(135deg, ${c1}, ${c2})`,
                    display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center",
                    boxShadow: `0 4px 18px ${c1}38`,
                  }}>
                    <span style={{
                      fontSize: 9, fontWeight: 700,
                      color: "rgba(255,255,255,.75)",
                      letterSpacing: ".14em",
                    }}>
                      {monthAbbr(t.start_date)}
                    </span>
                    <span style={{
                      fontFamily: "'Montserrat Alternates', sans-serif",
                      fontSize: 24, fontWeight: 800,
                      color: "#fff", lineHeight: 1,
                      letterSpacing: "-.04em",
                    }}>
                      {dayNum(t.start_date)}
                    </span>
                  </div>

                  {/* Details */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6, flexWrap: "wrap" }}>
                      <h3 style={{
                        fontSize: 14, fontWeight: 700,
                        color: "var(--text)", letterSpacing: "-.3px", margin: 0,
                      }}>
                        {t.name}
                      </h3>
                      <span style={{
                        fontSize: 10, fontWeight: 700, padding: "2px 10px", borderRadius: 99,
                        background: `${c1}16`, color: c1,
                        border: `1px solid ${c1}30`,
                        flexShrink: 0, textTransform: "uppercase", letterSpacing: ".5px",
                      }}>
                        {cat.label}
                      </span>
                    </div>

                    <div style={{
                      display: "flex", alignItems: "center", gap: 6,
                      fontSize: 11, color: "var(--text-muted)", marginBottom: 6, flexWrap: "wrap",
                    }}>
                      <MapPin size={10} style={{ flexShrink: 0, color: "var(--text-dim)" }} />
                      <span style={{ fontWeight: 600, color: "var(--text-muted)" }}>{t.city ?? "TBD"}</span>
                      {t.venue && (
                        <>
                          <span style={{ color: "var(--border-strong)" }}>·</span>
                          <span style={{ color: "var(--text-dim)" }}>{t.venue}</span>
                        </>
                      )}
                      <span style={{ color: "var(--border-strong)" }}>·</span>
                      <span style={{ color: "var(--text-dim)" }}>
                        {fmt(t.start_date)}
                        {t.end_date && t.end_date !== t.start_date ? ` – ${fmt(t.end_date)}` : ""}
                      </span>
                    </div>

                    {t.relevance_note && (
                      <p style={{ fontSize: 12, color: "var(--text-dim)", fontStyle: "italic", margin: 0 }}>
                        {t.relevance_note}
                      </p>
                    )}
                  </div>

                  {/* Countdown + link */}
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 10, flexShrink: 0 }}>
                    {until && (
                      <span style={{
                        fontSize: 11, fontWeight: 700, padding: "4px 12px", borderRadius: 99,
                        background: `${c1}16`, color: c1,
                        border: `1px solid ${c1}28`,
                        whiteSpace: "nowrap",
                      }}>
                        {until}
                      </span>
                    )}
                    <div style={{ display: "flex", gap: 12, alignItems: "center", justifyContent: "flex-end" }}>
                      <SaveButton
                        itemType="trade_show"
                        itemId={t.id}
                        title={t.name}
                        content={t}
                      />
                      {t.website && (
                        <a
                          href={t.website}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: "var(--text-dim)", transition: "color .2s" }}
                          onMouseEnter={e => e.currentTarget.style.color = "var(--blue)"}
                          onMouseLeave={e => e.currentTarget.style.color = "var(--text-dim)"}
                        >
                          <ExternalLink size={14} />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
        }
      </div>
    </div>
  );
}
