import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { ExternalLink, Users } from "lucide-react";

// Deterministic gradient per competitor name
const GRADIENTS = [
  ["#6366f1", "#8b5cf6"],
  ["#ef4444", "#f97316"],
  ["#22c55e", "#14b8a6"],
  ["#3b82f6", "#6366f1"],
  ["#f59e0b", "#ef4444"],
  ["#ec4899", "#8b5cf6"],
  ["#14b8a6", "#3b82f6"],
  ["#f97316", "#f59e0b"],
];

function gradient(name) {
  const [a, b] = GRADIENTS[(name?.charCodeAt(0) ?? 0) % GRADIENTS.length];
  return `linear-gradient(135deg, ${a}, ${b})`;
}

function SkeletonCard() {
  return (
    <div className="glass-card p-6" style={{ minHeight: 140 }}>
      <div className="flex items-center gap-4 mb-4">
        <div className="shimmer rounded-2xl" style={{ width: 48, height: 48, flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <div className="shimmer rounded" style={{ height: 16, width: "60%", marginBottom: 8 }} />
          <div className="shimmer rounded-full" style={{ height: 20, width: 52 }} />
        </div>
      </div>
      <div className="shimmer rounded" style={{ height: 13, width: "80%", marginBottom: 8 }} />
      <div className="shimmer rounded" style={{ height: 13, width: "55%" }} />
    </div>
  );
}

export default function Competitors() {
  const [competitors, setCompetitors] = useState([]);
  const [loading, setLoading]         = useState(true);

  useEffect(() => {
    api.competitors()
      .then(setCompetitors)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-extrabold" style={{ color: "#0f172a", letterSpacing: "-0.02em" }}>
            Competitors
          </h2>
          <p className="text-sm font-medium mt-1" style={{ color: "#94a3b8" }}>
            {loading ? "Loading…" : `${competitors.length} platforms being monitored`}
          </p>
        </div>
        <div style={{
          display: "flex", alignItems: "center", gap: 8,
          padding: "8px 16px", borderRadius: 99,
          background: "rgba(99, 102, 241, 0.08)",
          border: "1px solid rgba(99, 102, 241, 0.15)",
        }}>
          <Users size={14} style={{ color: "#6366f1" }} />
          <span style={{ fontSize: 12, fontWeight: 600, color: "#4f46e5" }}>Active watch list</span>
        </div>
      </div>

      {/* Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
          : competitors.map((c) => (
            <div
              key={c.id}
              className="glass-card"
              style={{ padding: 24 }}
            >
              {/* Avatar + name row */}
              <div style={{ display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 16 }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 14, flexShrink: 0,
                  background: gradient(c.name),
                  display: "flex", alignItems: "center", justifyContent: "center",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.12)",
                  fontSize: 18, fontWeight: 800, color: "#fff",
                  letterSpacing: "-0.02em",
                }}>
                  {c.name?.[0] ?? "?"}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <h3 style={{
                    fontSize: 15, fontWeight: 700, color: "#0f172a",
                    marginBottom: 6, letterSpacing: "-0.01em",
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                  }}>
                    {c.name}
                  </h3>
                  <span style={{
                    fontSize: 11, fontWeight: 600, padding: "2px 10px",
                    borderRadius: 99, background: "rgba(34, 197, 94, 0.1)",
                    color: "#16a34a", border: "1px solid rgba(34, 197, 94, 0.2)",
                  }}>
                    Active
                  </span>
                </div>
              </div>

              {/* Links */}
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {c.website && (
                  <a
                    href={c.website}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      display: "flex", alignItems: "center", gap: 6,
                      fontSize: 12, fontWeight: 500, color: "#6366f1",
                      textDecoration: "none", overflow: "hidden",
                    }}
                    onMouseEnter={e => e.currentTarget.style.textDecoration = "underline"}
                    onMouseLeave={e => e.currentTarget.style.textDecoration = "none"}
                  >
                    <ExternalLink size={11} style={{ flexShrink: 0 }} />
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {c.website.replace(/^https?:\/\//, "")}
                    </span>
                  </a>
                )}
                {c.play_store_id && (
                  <p style={{ fontSize: 12, color: "#94a3b8", margin: 0 }}>
                    Play Store:{" "}
                    <span style={{ fontFamily: "monospace", color: "#64748b" }}>{c.play_store_id}</span>
                  </p>
                )}
                {c.linkedin_url && (
                  <a
                    href={c.linkedin_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: 12, fontWeight: 500, color: "#3b82f6", textDecoration: "none" }}
                  >
                    LinkedIn →
                  </a>
                )}
              </div>
            </div>
          ))
        }
      </div>
    </div>
  );
}
