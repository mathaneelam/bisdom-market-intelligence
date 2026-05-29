import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { AlertCircle, TrendingUp, Zap, BarChart2, ArrowUpRight, Clock } from "lucide-react";

/* ── Stat card ───────────────────────────────────────────── */
function StatCard({ icon: Icon, label, value, accentColor, delay }) {
  return (
    <div
      className={`glass-card animate-fade-in-delay-${delay}`}
      style={{ padding: "26px 28px", overflow: "hidden", position: "relative" }}
    >
      {/* Icon + label */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 18, position: "relative" }}>
        <div style={{
          width: 38, height: 38, borderRadius: 10, flexShrink: 0,
          background: `${accentColor}18`,
          border: `1px solid ${accentColor}30`,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <Icon size={16} style={{ color: accentColor }} />
        </div>
        <p className="section-label" style={{ margin: 0 }}>{label}</p>
      </div>

      {/* Number */}
      <p style={{
        fontFamily: "'Montserrat Alternates', sans-serif",
        fontSize: 32,
        fontWeight: 800,
        letterSpacing: "-1.5px",
        color: "var(--text)",
        margin: 0,
        position: "relative",
      }}>
        {value ?? <span className="shimmer" style={{ display: "inline-block", width: 60, height: 36, verticalAlign: "middle" }} />}
      </p>
    </div>
  );
}

/* ── Brief section card ──────────────────────────────────── */
function BriefSection({ title, dotColor, items, accentColor }) {
  const empty = !items || items.length === 0;
  return (
    <div className="glass-card" style={{ padding: "24px 26px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 18 }}>
        <span style={{
          width: 8, height: 8, borderRadius: "50%",
          background: dotColor, display: "inline-block", flexShrink: 0,
        }} />
        <h3 style={{
          fontSize: 13,
          fontWeight: 700,
          color: "var(--text)",
          margin: 0,
          letterSpacing: "-.2px",
        }}>
          {title}
        </h3>
      </div>

      {empty ? (
        <p style={{ fontSize: 13, fontStyle: "italic", color: "var(--text-dim)", margin: 0 }}>
          No signals above threshold yet.
        </p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 10 }}>
          {items.map((s, i) => (
            <li
              key={i}
              style={{
                padding: "14px 16px",
                borderRadius: 12,
                background: `${accentColor}08`,
                borderLeft: `2px solid ${accentColor}60`,
                transition: "transform .2s, background .2s",
                cursor: "default",
              }}
              onMouseEnter={e => {
                e.currentTarget.style.transform = "translateX(4px)";
                e.currentTarget.style.background = `${accentColor}12`;
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = "translateX(0)";
                e.currentTarget.style.background = `${accentColor}08`;
              }}
            >
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 10, marginBottom: 6 }}>
                <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", margin: 0, lineHeight: 1.45, letterSpacing: "-.2px" }}>
                  {s.summary}
                </p>
                <span style={{
                  fontSize: 11, fontWeight: 700,
                  padding: "3px 8px", borderRadius: 6, flexShrink: 0,
                  background: `${accentColor}18`,
                  color: accentColor,
                }}>
                  {s.relevance_score}/10
                </span>
              </div>
              <p style={{ fontSize: 12, color: "var(--text-muted)", margin: 0, lineHeight: 1.6 }}>
                {s.insight}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* ── Skeleton loader ─────────────────────────────────────── */
function DashboardSkeleton() {
  return (
    <div>
      <div className="shimmer" style={{ height: 28, width: 160, marginBottom: 8 }} />
      <div className="shimmer" style={{ height: 14, width: 220, marginBottom: 36 }} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, marginBottom: 36 }}>
        {[1,2,3,4].map(i => (
          <div key={i} className="glass-card" style={{ padding: 26 }}>
            <div className="shimmer" style={{ height: 38, width: 38, borderRadius: 10, marginBottom: 18 }} />
            <div className="shimmer" style={{ height: 36, width: 80 }} />
          </div>
        ))}
      </div>
      <div className="shimmer" style={{ height: 18, width: 220, marginBottom: 20 }} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
        {[1,2,3].map(i => (
          <div key={i} className="glass-card" style={{ padding: 26 }}>
            <div className="shimmer" style={{ height: 14, width: 100, marginBottom: 18 }} />
            <div className="shimmer" style={{ height: 80, width: "100%" }} />
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────── */
export default function Dashboard() {
  const [stats, setStats]     = useState(null);
  const [brief, setBrief]     = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.signalStats(), api.todayBrief()])
      .then(([s, b]) => { setStats(s); setBrief(b); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <DashboardSkeleton />;

  const today = new Date().toLocaleDateString("en-IN", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });

  return (
    <div className="animate-fade-in">

      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 36 }}>
        <div>
          <p className="section-label">Overview</p>
          <h2 style={{
            fontFamily: "'Montserrat Alternates', sans-serif",
            fontSize: 28,
            fontWeight: 800,
            color: "var(--text)",
            letterSpacing: "-1.2px",
            margin: "0 0 8px",
          }}>
            Dashboard
          </h2>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Clock size={12} style={{ color: "var(--text-dim)" }} />
            <span style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 500 }}>{today}</span>
          </div>
        </div>

        {/* Live badge */}
        <div style={{
          display: "flex", alignItems: "center", gap: 7,
          padding: "7px 14px", borderRadius: 99,
          background: "var(--green-tint)",
          border: "1px solid var(--green-border)",
        }}>
          <span className="pulse-dot" style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--green)", display: "inline-block" }} />
          <span style={{ fontSize: 11, fontWeight: 700, color: "var(--green)", letterSpacing: ".5px", textTransform: "uppercase" }}>Live</span>
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, marginBottom: 36 }}>
        <StatCard icon={BarChart2}   label="Total Signals"   value={stats?.total}             accentColor="#1889F6" delay={1} />
        <StatCard icon={AlertCircle} label="Pain Pulse"      value={stats?.pain_pulse}         accentColor="#EF4444" delay={2} />
        <StatCard icon={TrendingUp}  label="Competitor Move" value={stats?.competitor_move}    accentColor="#1889F6" delay={3} />
        <StatCard icon={Zap}         label="Opportunity"     value={stats?.opportunity_signal} accentColor="#22C55E" delay={4} />
      </div>

      <div className="divider" style={{ marginBottom: 36 }} />

      {/* Brief */}
      <div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <div>
            <p className="section-label">Intelligence</p>
            <h2 style={{
              fontFamily: "'Montserrat Alternates', sans-serif",
              fontSize: 20,
              fontWeight: 800,
              color: "var(--text)",
              letterSpacing: "-.6px",
              margin: 0,
            }}>
              Today's Brief
            </h2>
          </div>

          {brief?.brief ? (
            <span style={{
              display: "flex", alignItems: "center", gap: 5,
              fontSize: 11, fontWeight: 700,
              padding: "6px 14px", borderRadius: 99,
              background: "var(--green-tint)",
              color: "var(--green)",
              border: "1px solid var(--green-border)",
              textTransform: "uppercase", letterSpacing: ".5px",
            }}>
              <ArrowUpRight size={11} />
              Generated
            </span>
          ) : (
            <span style={{
              fontSize: 11, fontWeight: 600,
              padding: "6px 14px", borderRadius: 99,
              background: "var(--blue-tint)",
              color: "var(--text-dim)",
              border: "1px solid var(--border-card)",
            }}>
              Not generated yet
            </span>
          )}
        </div>

        {brief?.brief ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
            <BriefSection title="Pain Pulse"      dotColor="#EF4444" items={brief.brief.pain_pulse}      accentColor="#EF4444" />
            <BriefSection title="Competitor Move" dotColor="#1889F6" items={brief.brief.competitor_move} accentColor="#1889F6" />
            <BriefSection title="Opportunity"     dotColor="#22C55E" items={brief.brief.opportunity}     accentColor="#22C55E" />
          </div>
        ) : (
          <div className="glass-card" style={{ padding: "48px 32px", textAlign: "center" }}>
            <p style={{ fontSize: 13, fontStyle: "italic", color: "var(--text-dim)", margin: 0 }}>
              Brief is generated daily at 5:30 AM IST after AI processing. Collect signals first, then run{" "}
              <code style={{ color: "var(--blue)", fontFamily: "monospace", fontSize: 12 }}>POST /trigger/brief</code>.
            </p>
          </div>
        )}
      </div>

    </div>
  );
}
