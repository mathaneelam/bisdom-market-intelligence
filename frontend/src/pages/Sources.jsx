import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { 
  Instagram, 
  MessageSquare, 
  Newspaper, 
  Smartphone, 
  Globe, 
  Radio, 
  Database
} from "lucide-react";

const STREAM_META = {
  pain_pulse:         { label: "Pain Pulse",      color: "#EF4444" },
  competitor_move:    { label: "Competitor Move", color: "#1889F6" },
  opportunity_signal: { label: "Opportunity",     color: "#22C55E" },
};

function StreamBadge({ stream }) {
  const meta = STREAM_META[stream];
  if (!meta) return <span style={{ color: "var(--text-dim)", fontSize: 11 }}>—</span>;
  return (
    <span style={{
      fontSize: 11, fontWeight: 700,
      padding: "3px 10px", borderRadius: 99,
      background: `${meta.color}14`,
      color: meta.color,
      border: `1px solid ${meta.color}28`,
      whiteSpace: "nowrap",
      letterSpacing: ".3px",
    }}>
      {meta.label}
    </span>
  );
}

function ProcessedDot({ yes }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      fontSize: 11, fontWeight: 600,
      color: yes ? "var(--green)" : "var(--text-dim)",
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: "50%",
        background: yes ? "var(--green)" : "var(--text-dim)",
        display: "inline-block",
      }} />
      {yes ? "Yes" : "No"}
    </span>
  );
}

function fmt(dt) {
  if (!dt) return "—";
  return new Date(dt).toLocaleString("en-IN", {
    day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  });
}

function SkeletonRow() {
  return (
    <tr>
      {[90, 280, 90, 110, 50].map((w, i) => (
        <td key={i} style={{ padding: "14px 20px" }}>
          <div className="shimmer" style={{ height: 18, width: w, borderRadius: 99 }} />
        </td>
      ))}
    </tr>
  );
}

function getSourceIcon(source) {
  const name = source.toLowerCase();
  if (name.includes("instagram")) return Instagram;
  if (name.includes("reddit")) return MessageSquare;
  if (name.includes("news")) return Newspaper;
  if (name.includes("play store")) return Smartphone;
  return Globe;
}

const PAGE_SIZE = 50;

export default function Sources() {
  const [sourcesList, setSourcesList] = useState([]);
  const [activeSource, setActiveSource] = useState(null);
  const [data, setData] = useState(null);
  const [offset, setOffset] = useState(0);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingSignals, setLoadingSignals] = useState(false);

  // Fetch unique sources and counts on mount
  useEffect(() => {
    setLoadingList(true);
    api.sources()
      .then((res) => {
        setSourcesList(res);
        if (res && res.length > 0) {
          // Default to the source with the highest count
          setActiveSource(res[0].source);
        }
      })
      .catch(console.error)
      .finally(() => setLoadingList(false));
  }, []);

  // Fetch signals when activeSource or offset changes
  useEffect(() => {
    if (!activeSource) return;
    setLoadingSignals(true);
    api.signals(null, PAGE_SIZE, offset, activeSource)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoadingSignals(false));
  }, [activeSource, offset]);

  const selectSource = (sourceName) => {
    setActiveSource(sourceName);
    setOffset(0);
  };

  const total = data?.total ?? 0;
  const items = data?.items ?? [];

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <p className="section-label">Inventory</p>
        <h2 style={{
          fontFamily: "'Montserrat Alternates', sans-serif",
          fontSize: 28, fontWeight: 800,
          color: "var(--text)", letterSpacing: "-1.2px",
          margin: "0 0 6px",
        }}>
          Sources
        </h2>
        <p style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 500, margin: 0 }}>
          View and analyze signals classified by where they were collected
        </p>
      </div>

      {/* Sources Grid */}
      {loadingList ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16, marginBottom: 32 }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="glass-card shimmer" style={{ height: 110, borderRadius: 16 }} />
          ))}
        </div>
      ) : (
        <div style={{ 
          display: "grid", 
          gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", 
          gap: 16, 
          marginBottom: 36 
        }}>
          {sourcesList.map((item) => {
            const isActive = activeSource === item.source;
            const IconComponent = getSourceIcon(item.source);
            return (
              <button
                key={item.source}
                onClick={() => selectSource(item.source)}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "flex-start",
                  padding: "20px 24px",
                  borderRadius: 16,
                  border: isActive ? "1px solid rgba(24, 137, 246, 0.35)" : "1px solid var(--border-card)",
                  background: isActive ? "var(--blue-tint)" : "rgba(255, 255, 255, 0.02)",
                  color: "var(--text)",
                  textAlign: "left",
                  cursor: "pointer",
                  transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
                  boxShadow: isActive ? "0 4px 20px -4px rgba(24, 137, 246, 0.15)" : "none",
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)";
                    e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.15)";
                    e.currentTarget.style.transform = "translateY(-2px)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = "rgba(255, 255, 255, 0.02)";
                    e.currentTarget.style.borderColor = "var(--border-card)";
                    e.currentTarget.style.transform = "none";
                  }
                }}
              >
                <div style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 36,
                  height: 36,
                  borderRadius: "50%",
                  background: isActive ? "rgba(24, 137, 246, 0.12)" : "rgba(255, 255, 255, 0.04)",
                  color: isActive ? "var(--blue)" : "var(--text-muted)",
                  marginBottom: 16,
                  transition: "all 0.2s",
                }}>
                  <IconComponent size={18} />
                </div>
                <span style={{ 
                  fontSize: 14, 
                  fontWeight: 700, 
                  color: isActive ? "var(--text)" : "var(--text-muted)",
                  marginBottom: 4 
                }}>
                  {item.source}
                </span>
                <span style={{ 
                  fontSize: 11, 
                  fontWeight: 600, 
                  color: isActive ? "var(--blue)" : "var(--text-dim)" 
                }}>
                  {item.count.toLocaleString()} signals
                </span>
              </button>
            );
          })}
        </div>
      )}

      {/* Signals Table */}
      {activeSource && (
        <>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
            <h3 style={{
              fontFamily: "'Montserrat Alternates', sans-serif",
              fontSize: 18, fontWeight: 700,
              color: "var(--text)", letterSpacing: "-.5px",
              margin: 0
            }}>
              {activeSource} Signals
            </h3>
            {total > 0 && (
              <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-dim)" }}>
                Showing {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total.toLocaleString()}
              </span>
            )}
          </div>

          <div className="glass-card" style={{ overflow: "hidden", padding: 0 }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-card)" }}>
                  {["Stream", "Snippet", "Author", "Collected", "Processed"].map(h => (
                    <th key={h} style={{
                      padding: "12px 20px", textAlign: "left",
                      fontSize: 10, fontWeight: 700,
                      letterSpacing: "1.5px", textTransform: "uppercase",
                      color: "var(--text-dim)",
                      background: "rgba(255,255,255,.02)",
                    }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loadingSignals ? (
                  Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)
                ) : items.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: "64px 20px", textAlign: "center" }}>
                      <Radio size={32} style={{ color: "var(--text-dim)", margin: "0 auto 12px", display: "block" }} />
                      <p style={{ color: "var(--text-dim)", fontSize: 13, fontStyle: "italic", margin: 0 }}>
                        No signals collected from {activeSource} yet.
                      </p>
                    </td>
                  </tr>
                ) : items.map(s => (
                  <tr
                    key={s.id}
                    style={{ borderBottom: "1px solid var(--border-card)", transition: "background .15s" }}
                    onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,.025)"}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                  >
                    <td style={{ padding: "13px 20px", whiteSpace: "nowrap" }}>
                      <StreamBadge stream={s.stream} />
                    </td>
                    <td style={{ padding: "13px 20px", color: "var(--text-muted)", maxWidth: 380 }}>
                      <span title={s.snippet} style={{
                        display: "block", overflow: "hidden",
                        textOverflow: "ellipsis", whiteSpace: "nowrap", fontSize: 12,
                      }}>
                        {s.snippet || "—"}
                      </span>
                    </td>
                    <td style={{ padding: "13px 20px", color: "var(--text-dim)", whiteSpace: "nowrap", fontSize: 12 }}>
                      {s.author ?? "—"}
                    </td>
                    <td style={{ padding: "13px 20px", color: "var(--text-dim)", whiteSpace: "nowrap", fontSize: 12 }}>
                      {fmt(s.collected_at)}
                    </td>
                    <td style={{ padding: "13px 20px" }}>
                      <ProcessedDot yes={s.is_processed} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {total > PAGE_SIZE && (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 20 }}>
              <button
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                disabled={offset === 0}
                className="glass-card"
                style={{
                  padding: "9px 22px", fontSize: 12, fontWeight: 700,
                  color: "var(--text-muted)", border: "none", cursor: "pointer",
                  opacity: offset === 0 ? .35 : 1,
                }}
              >
                ← Previous
              </button>
              <button
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={offset + PAGE_SIZE >= total}
                className="glass-card"
                style={{
                  padding: "9px 22px", fontSize: 12, fontWeight: 700,
                  color: "var(--text-muted)", border: "none", cursor: "pointer",
                  opacity: offset + PAGE_SIZE >= total ? .35 : 1,
                }}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
