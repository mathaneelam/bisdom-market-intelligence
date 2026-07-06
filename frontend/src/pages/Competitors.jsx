import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { ExternalLink, Users } from "lucide-react";
import SaveButton from "../components/SaveButton";

// Deterministic gradient per competitor name (electric-blue palette)
const GRADIENTS = [
  ["#1889F6", "#0A4FC4"],
  ["#0A4FC4", "#0D2A6E"],
  ["#1889F6", "#3B82F6"],
  ["#0D2A6E", "#1889F6"],
  ["#3B82F6", "#60A5FA"],
  ["#1889F6", "#22C55E"],
  ["#0A4FC4", "#1889F6"],
  ["#22C55E", "#1889F6"],
];

function gradient(name) {
  const [a, b] = GRADIENTS[(name?.charCodeAt(0) ?? 0) % GRADIENTS.length];
  return `linear-gradient(135deg, ${a}, ${b})`;
}

function SkeletonCard() {
  return (
    <div className="glass-card" style={{ padding: 24, minHeight: 140 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 18 }}>
        <div className="shimmer" style={{ width: 48, height: 48, borderRadius: 14, flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <div className="shimmer" style={{ height: 14, width: "60%", marginBottom: 8 }} />
          <div className="shimmer" style={{ height: 20, width: 52, borderRadius: 99 }} />
        </div>
      </div>
      <div className="shimmer" style={{ height: 12, width: "75%", marginBottom: 8 }} />
      <div className="shimmer" style={{ height: 12, width: "50%" }} />
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
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 32 }}>
        <div>
          <p className="section-label">Watch List</p>
          <h2 style={{
            fontFamily: "'Montserrat Alternates', sans-serif",
            fontSize: 28, fontWeight: 800,
            color: "var(--text)", letterSpacing: "-1.2px",
            margin: "0 0 6px",
          }}>
            Competitors
          </h2>
          <p style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 500, margin: 0 }}>
            {loading ? "Loading…" : `${competitors.length} platforms being monitored`}
          </p>
        </div>
        <div style={{
          display: "flex", alignItems: "center", gap: 7,
          padding: "7px 16px", borderRadius: 99,
          background: "var(--blue-tint)",
          border: "1px solid rgba(24,137,246,.18)",
        }}>
          <Users size={13} style={{ color: "var(--blue)" }} />
          <span style={{ fontSize: 11, fontWeight: 700, color: "var(--blue)", textTransform: "uppercase", letterSpacing: ".8px" }}>
            Active Watch
          </span>
        </div>
      </div>

      {/* Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
          : competitors.map(c => (
            <div key={c.id} className="glass-card" style={{ padding: 24 }}>

              {/* Avatar + name */}
              <div style={{ display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 18 }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 14, flexShrink: 0,
                  background: gradient(c.name),
                  display: "flex", alignItems: "center", justifyContent: "center",
                  boxShadow: "0 4px 18px rgba(24,137,246,.22)",
                  fontSize: 18, fontWeight: 800, color: "#fff",
                  fontFamily: "'Montserrat Alternates', sans-serif",
                  letterSpacing: "-.02em",
                }}>
                  {c.name?.[0] ?? "?"}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <h3 style={{
                    fontSize: 14, fontWeight: 700, color: "var(--text)",
                    marginBottom: 7, letterSpacing: "-.3px",
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                  }}>
                    {c.name}
                  </h3>
                  <span style={{
                    fontSize: 10, fontWeight: 700, padding: "2px 10px",
                    borderRadius: 99,
                    background: "var(--green-tint)",
                    color: "var(--green)",
                    border: "1px solid var(--green-border)",
                    textTransform: "uppercase", letterSpacing: ".8px",
                  }}>
                    Active
                  </span>
                </div>

                <SaveButton
                  itemType="competitor"
                  itemId={c.id}
                  title={c.name}
                  content={c}
                />
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
                      fontSize: 12, fontWeight: 600, color: "var(--blue)",
                      textDecoration: "none", overflow: "hidden",
                      transition: "opacity .2s",
                    }}
                    onMouseEnter={e => e.currentTarget.style.opacity = ".7"}
                    onMouseLeave={e => e.currentTarget.style.opacity = "1"}
                  >
                    <ExternalLink size={11} style={{ flexShrink: 0 }} />
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {c.website.replace(/^https?:\/\//, "")}
                    </span>
                  </a>
                )}
                {c.play_store_id && (
                  <p style={{ fontSize: 11, color: "var(--text-dim)", margin: 0 }}>
                    Play Store:{" "}
                    <span style={{ fontFamily: "monospace", color: "var(--text-muted)" }}>
                      {c.play_store_id}
                    </span>
                  </p>
                )}
                {c.linkedin_url && (
                  <a
                    href={c.linkedin_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      fontSize: 12, fontWeight: 600,
                      color: "var(--blue)", textDecoration: "none",
                      transition: "opacity .2s",
                    }}
                    onMouseEnter={e => e.currentTarget.style.opacity = ".7"}
                    onMouseLeave={e => e.currentTarget.style.opacity = "1"}
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
