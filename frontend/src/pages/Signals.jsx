import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Radio, ExternalLink } from "lucide-react";

const STREAMS = [
  { value: "",                   label: "All",             color: "#1889F6" },
  { value: "pain_pulse",         label: "Pain Pulse",      color: "#EF4444" },
  { value: "competitor_move",    label: "Competitor Move", color: "#1889F6" },
  { value: "opportunity_signal", label: "Opportunity",     color: "#22C55E" },
];

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

const formatUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("playstore://")) {
    const parts = url.replace("playstore://", "").split("/");
    const pkg = parts[0];
    return `https://play.google.com/store/apps/details?id=${pkg}`;
  }
  return url;
};

function SkeletonRow() {
  return (
    <tr>
      {[90, 100, 280, 90, 110, 50].map((w, i) => (
        <td key={i} style={{ padding: "14px 20px" }}>
          <div className="shimmer" style={{ height: 18, width: w, borderRadius: 99 }} />
        </td>
      ))}
    </tr>
  );
}

const PAGE_SIZE = 50;

export default function Signals() {
  const [stream, setStream]   = useState("");
  const [data, setData]       = useState(null);
  const [offset, setOffset]   = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.signals(stream || null, PAGE_SIZE, offset)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [stream, offset]);

  function changeStream(v) { setStream(v); setOffset(0); }

  const total = data?.total ?? 0;
  const items = data?.items ?? [];

  return (
    <div className="animate-fade-in">

      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 32 }}>
        <div>
          <p className="section-label">Data</p>
          <h2 style={{
            fontFamily: "'Montserrat Alternates', sans-serif",
            fontSize: 28, fontWeight: 800,
            color: "var(--text)", letterSpacing: "-1.2px",
            margin: "0 0 6px",
          }}>
            Signals
          </h2>
          <p style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 500, margin: 0 }}>
            Every signal collected from every source
          </p>
        </div>
        {total > 0 && (
          <div style={{
            padding: "7px 16px", borderRadius: 99,
            background: "var(--blue-tint)",
            border: "1px solid rgba(24,137,246,.18)",
          }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--blue)" }}>
              {total.toLocaleString()} signals
            </span>
          </div>
        )}
      </div>

      {/* Filter pills */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
        {STREAMS.map(({ value, label, color }) => {
          const isActive = stream === value;
          return (
            <button
              key={value}
              onClick={() => changeStream(value)}
              style={{
                padding: "7px 18px", borderRadius: 99,
                fontSize: 12, fontWeight: 600,
                border: isActive ? `1px solid ${color}35` : "1px solid var(--border-card)",
                cursor: "pointer", transition: "all .2s",
                background: isActive ? `${color}14` : "transparent",
                color: isActive ? color : "var(--text-muted)",
                letterSpacing: ".2px",
              }}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Table */}
      <div className="glass-card" style={{ overflow: "hidden", padding: 0 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-card)" }}>
              {["Stream", "Source", "Snippet", "Author", "Collected", "Processed"].map(h => (
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
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} />)
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: "64px 20px", textAlign: "center" }}>
                  <Radio size={32} style={{ color: "var(--text-dim)", margin: "0 auto 12px", display: "block" }} />
                  <p style={{ color: "var(--text-dim)", fontSize: 13, fontStyle: "italic", margin: 0 }}>
                    No signals yet. Run a collector to start pulling data.
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
                <td style={{ padding: "13px 20px", color: "var(--text)", fontWeight: 600, whiteSpace: "nowrap", fontSize: 12 }}>
                  {s.source ?? "—"}
                </td>
                <td style={{ padding: "13px 20px", color: "var(--text-muted)", maxWidth: 320 }}>
                  {s.source_url ? (
                    <a 
                      href={formatUrl(s.source_url)} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      style={{ 
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 6,
                        color: "var(--text-muted)", 
                        textDecoration: "none",
                        transition: "color .15s"
                      }}
                      onMouseEnter={e => e.currentTarget.style.color = "var(--blue)"}
                      onMouseLeave={e => e.currentTarget.style.color = "var(--text-muted)"}
                    >
                      <span title={s.snippet} style={{
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        fontSize: 12,
                      }}>
                        {s.snippet || "—"}
                      </span>
                      <ExternalLink size={12} style={{ opacity: 0.6, flexShrink: 0 }} />
                    </a>
                  ) : (
                    <span title={s.snippet} style={{
                      display: "block",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      fontSize: 12,
                    }}>
                      {s.snippet || "—"}
                    </span>
                  )}
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
          <span style={{ fontSize: 12, color: "var(--text-dim)", fontWeight: 600 }}>
            {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total.toLocaleString()}
          </span>
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
    </div>
  );
}
