import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Radio } from "lucide-react";

const STREAMS = [
  { value: "",                   label: "All",             color: "#6366f1" },
  { value: "pain_pulse",         label: "Pain Pulse",      color: "#ef4444" },
  { value: "competitor_move",    label: "Competitor Move", color: "#3b82f6" },
  { value: "opportunity_signal", label: "Opportunity",     color: "#22c55e" },
];

const STREAM_META = {
  pain_pulse:         { label: "Pain Pulse",      color: "#ef4444" },
  competitor_move:    { label: "Competitor Move", color: "#3b82f6" },
  opportunity_signal: { label: "Opportunity",     color: "#22c55e" },
};

function StreamBadge({ stream }) {
  const meta = STREAM_META[stream];
  if (!meta) return <span style={{ color: "#94a3b8", fontSize: 11 }}>—</span>;
  return (
    <span style={{
      fontSize: 11,
      fontWeight: 600,
      padding: "3px 10px",
      borderRadius: 99,
      background: `${meta.color}18`,
      color: meta.color,
      border: `1px solid ${meta.color}30`,
      whiteSpace: "nowrap",
    }}>
      {meta.label}
    </span>
  );
}

function ProcessedDot({ yes }) {
  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 5,
      fontSize: 11,
      fontWeight: 500,
      color: yes ? "#16a34a" : "#94a3b8",
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: "50%",
        background: yes ? "#22c55e" : "#cbd5e1",
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
      {[100, 80, 280, 90, 110, 50].map((w, i) => (
        <td key={i} className="px-5 py-4">
          <div className="shimmer rounded-full" style={{ height: 18, width: w }} />
        </td>
      ))}
    </tr>
  );
}

const PAGE_SIZE = 50;

export default function Signals() {
  const [stream, setStream]     = useState("");
  const [data, setData]         = useState(null);
  const [offset, setOffset]     = useState(0);
  const [loading, setLoading]   = useState(true);

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
  const active = STREAMS.find(s => s.value === stream) ?? STREAMS[0];

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-extrabold" style={{ color: "#0f172a", letterSpacing: "-0.02em" }}>
            Signals
          </h2>
          <p className="text-sm font-medium mt-1" style={{ color: "#94a3b8" }}>
            Every signal collected from every source
          </p>
        </div>
        {total > 0 && (
          <div className="px-4 py-2 rounded-full glass-card" style={{ boxShadow: "none" }}>
            <span className="text-sm font-semibold" style={{ color: "#334155" }}>
              {total.toLocaleString()} signals
            </span>
          </div>
        )}
      </div>

      {/* Stream filter */}
      <div className="flex gap-2 mb-5">
        {STREAMS.map(({ value, label, color }) => {
          const isActive = stream === value;
          return (
            <button
              key={value}
              onClick={() => changeStream(value)}
              style={{
                padding: "7px 18px",
                borderRadius: 99,
                fontSize: 13,
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
                transition: "all 0.2s",
                background: isActive ? `${color}18` : "rgba(255,255,255,0.7)",
                color: isActive ? color : "#64748b",
                boxShadow: isActive
                  ? `0 0 0 1.5px ${color}40, 0 2px 8px ${color}18`
                  : "0 1px 3px rgba(0,0,0,0.06)",
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
            <tr style={{ borderBottom: "1px solid rgba(226, 232, 240, 0.8)" }}>
              {["Stream", "Source", "Snippet", "Author", "Collected", "Processed"].map(h => (
                <th key={h} style={{
                  padding: "12px 20px",
                  textAlign: "left",
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  color: "#94a3b8",
                  background: "rgba(248, 250, 252, 0.6)",
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} />)
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: "60px 20px", textAlign: "center" }}>
                  <Radio size={32} style={{ color: "#e2e8f0", margin: "0 auto 12px" }} />
                  <p style={{ color: "#94a3b8", fontSize: 14, fontStyle: "italic" }}>
                    No signals yet. Run a collector to start pulling data.
                  </p>
                </td>
              </tr>
            ) : items.map((s, i) => (
              <tr
                key={s.id}
                style={{ borderBottom: "1px solid rgba(226, 232, 240, 0.5)", transition: "background 0.15s" }}
                onMouseEnter={e => e.currentTarget.style.background = "rgba(248, 250, 252, 0.7)"}
                onMouseLeave={e => e.currentTarget.style.background = "transparent"}
              >
                <td style={{ padding: "13px 20px", whiteSpace: "nowrap" }}>
                  <StreamBadge stream={s.stream} />
                </td>
                <td style={{ padding: "13px 20px", color: "#334155", fontWeight: 500, whiteSpace: "nowrap" }}>
                  {s.source ?? "—"}
                </td>
                <td style={{ padding: "13px 20px", color: "#64748b", maxWidth: 300 }}>
                  <span title={s.snippet} style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {s.snippet || "—"}
                  </span>
                </td>
                <td style={{ padding: "13px 20px", color: "#94a3b8", whiteSpace: "nowrap" }}>
                  {s.author ?? "—"}
                </td>
                <td style={{ padding: "13px 20px", color: "#94a3b8", whiteSpace: "nowrap" }}>
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
        <div className="flex items-center justify-between mt-5">
          <button
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            disabled={offset === 0}
            className="glass-card"
            style={{
              padding: "8px 20px", fontSize: 13, fontWeight: 600,
              color: "#334155", border: "none", cursor: "pointer",
              opacity: offset === 0 ? 0.35 : 1,
            }}
          >
            ← Previous
          </button>
          <span style={{ fontSize: 13, color: "#94a3b8", fontWeight: 500 }}>
            {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total.toLocaleString()}
          </span>
          <button
            onClick={() => setOffset(offset + PAGE_SIZE)}
            disabled={offset + PAGE_SIZE >= total}
            className="glass-card"
            style={{
              padding: "8px 20px", fontSize: 13, fontWeight: 600,
              color: "#334155", border: "none", cursor: "pointer",
              opacity: offset + PAGE_SIZE >= total ? 0.35 : 1,
            }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
