import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { AlertCircle, TrendingUp, Zap, BarChart2, ArrowUpRight, Clock, Layers, ChevronDown, ExternalLink } from "lucide-react";

/* ── Helpers ─────────────────────────────────────────────── */
function fmtDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}
function fmtDateTime(d) {
  if (!d) return "—";
  return new Date(d).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

/* ── Stat card ───────────────────────────────────────────── */
function StatCard({ icon: Icon, label, value, accentColor, delay }) {
  return (
    <div className={`glass-card animate-fade-in-delay-${delay}`} style={{ padding: "26px 28px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 18 }}>
        <div style={{
          width: 38, height: 38, borderRadius: 10, flexShrink: 0,
          background: `${accentColor}18`, border: `1px solid ${accentColor}30`,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <Icon size={16} style={{ color: accentColor }} />
        </div>
        <p className="section-label" style={{ margin: 0 }}>{label}</p>
      </div>
      <p style={{
        fontFamily: "'Montserrat Alternates', sans-serif",
        fontSize: 32, fontWeight: 800, letterSpacing: "-1.5px",
        color: "var(--text)", margin: 0,
      }}>
        {value ?? <span className="shimmer" style={{ display: "inline-block", width: 60, height: 36 }} />}
      </p>
    </div>
  );
}

/* ── Compact brief row ───────────────────────────────────── */
function BriefRow({ item, accentColor }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      style={{
        padding: "10px 16px", borderRadius: 10, cursor: "pointer",
        background: `${accentColor}06`, borderLeft: `2px solid ${accentColor}50`,
        transition: "background .2s",
      }}
      onClick={() => setOpen(!open)}
      onMouseEnter={e => e.currentTarget.style.background = `${accentColor}10`}
      onMouseLeave={e => e.currentTarget.style.background = `${accentColor}06`}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <p style={{ flex: 1, fontSize: 12, fontWeight: 600, color: "var(--text)", margin: 0, lineHeight: 1.4,
          overflow: open ? "visible" : "hidden", textOverflow: "ellipsis", whiteSpace: open ? "normal" : "nowrap",
        }}>
          {item.summary}
        </p>
        <span style={{
          fontSize: 10, fontWeight: 700, padding: "2px 7px", borderRadius: 5, flexShrink: 0,
          background: `${accentColor}18`, color: accentColor,
        }}>
          {item.relevance_score}/10
        </span>
        <ChevronDown size={12} style={{
          color: "var(--text-dim)", flexShrink: 0,
          transform: open ? "rotate(180deg)" : "rotate(0)", transition: "transform .2s",
        }} />
      </div>
      {open && (
        <p style={{ fontSize: 11, color: "var(--text-muted)", margin: "8px 0 0", lineHeight: 1.55 }}>
          {item.insight}
        </p>
      )}
    </div>
  );
}

/* ── Compact brief section ───────────────────────────────── */
function BriefStream({ title, dotColor, items, accentColor }) {
  if (!items || items.length === 0) return null;
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
        <span style={{ width: 6, height: 6, borderRadius: "50%", background: dotColor, display: "inline-block" }} />
        <span style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: ".8px" }}>
          {title}
        </span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {items.map((s, i) => <BriefRow key={i} item={s} accentColor={accentColor} />)}
      </div>
    </div>
  );
}

/* ── Expandable pattern card with sources ────────────────── */
function PatternCard({ pattern }) {
  const [open, setOpen] = useState(false);
  const [signals, setSignals] = useState(null);

  const catColor = pattern.category === "pain_pulse" ? "#EF4444"
    : pattern.category === "opportunity_signal" ? "#22C55E" : "#1889F6";
  const trendIcon = pattern.trend === "growing" ? "↑" : pattern.trend === "new" ? "★" : pattern.trend === "declining" ? "↓" : "→";
  const trendColor = pattern.trend === "growing" ? "#22C55E" : pattern.trend === "new" ? "#1889F6" : pattern.trend === "declining" ? "#EF4444" : "var(--text-dim)";

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && !signals) {
      try {
        const data = await api.patternSignals(pattern.id);
        setSignals(data);
      } catch (e) {
        console.error(e);
        setSignals([]);
      }
    }
  }

  return (
    <div className="glass-card" style={{ overflow: "hidden" }}>
      {/* Header row — clickable */}
      <div
        onClick={toggle}
        style={{
          padding: "14px 22px", display: "flex", alignItems: "center", gap: 16, cursor: "pointer",
          transition: "background .15s",
        }}
        onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,.02)"}
        onMouseLeave={e => e.currentTarget.style.background = "transparent"}
      >
        <div style={{ width: 4, height: 40, borderRadius: 4, flexShrink: 0,
          background: `linear-gradient(180deg, ${catColor}, ${catColor}40)`,
        }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{
            fontSize: 13, fontWeight: 700, color: "var(--text)", margin: "0 0 3px", letterSpacing: "-.2px",
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
          }}>
            {pattern.name}
          </p>
          <p style={{ fontSize: 10, color: "var(--text-dim)", margin: 0 }}>
            First seen {fmtDate(pattern.first_seen)} · Last {fmtDate(pattern.last_seen)}
          </p>
        </div>
        <div style={{
          display: "flex", alignItems: "center", gap: 5, padding: "4px 12px", borderRadius: 99, flexShrink: 0,
          background: `${catColor}12`, border: `1px solid ${catColor}25`,
        }}>
          <span style={{ fontSize: 14, fontWeight: 800, color: catColor, fontFamily: "'Montserrat Alternates', sans-serif" }}>
            {pattern.signal_count}
          </span>
          <span style={{ fontSize: 10, color: "var(--text-dim)", fontWeight: 600 }}>reports</span>
        </div>
        <span style={{
          fontSize: 11, fontWeight: 700, color: trendColor, padding: "3px 10px", borderRadius: 99,
          background: `${trendColor}12`, border: `1px solid ${trendColor}25`, whiteSpace: "nowrap", flexShrink: 0,
        }}>
          {trendIcon} {pattern.trend}
        </span>
        <ChevronDown size={14} style={{
          color: "var(--text-dim)", flexShrink: 0,
          transform: open ? "rotate(180deg)" : "rotate(0)", transition: "transform .2s",
        }} />
      </div>

      {/* Expanded: source signals */}
      {open && (
        <div style={{
          padding: "0 22px 16px",
          borderTop: "1px solid var(--border-card)",
        }}>
          {/* Bisdom action */}
          {pattern.bisdom_action && (
            <p style={{
              fontSize: 11, color: "var(--blue)", fontWeight: 600, fontStyle: "italic",
              margin: "12px 0 14px", padding: "8px 12px", borderRadius: 8,
              background: "var(--blue-tint)", border: "1px solid rgba(24,137,246,.15)",
            }}>
              Bisdom action: {pattern.bisdom_action}
            </p>
          )}

          {/* Source list */}
          {!signals ? (
            <div style={{ padding: "12px 0" }}>
              <div className="shimmer" style={{ height: 14, width: "70%", marginBottom: 10 }} />
              <div className="shimmer" style={{ height: 14, width: "55%" }} />
            </div>
          ) : signals.length === 0 ? (
            <p style={{ fontSize: 12, color: "var(--text-dim)", fontStyle: "italic", margin: "12px 0 0" }}>
              No linked signals found.
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 12 }}>
              {signals.map(s => (
                <div key={s.id} style={{
                  padding: "10px 14px", borderRadius: 8,
                  background: "rgba(255,255,255,.02)", border: "1px solid var(--border-card)",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, flexWrap: "wrap" }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text)" }}>
                      {s.author || "Unknown"}
                    </span>
                    <span style={{ fontSize: 10, color: "var(--text-dim)" }}>·</span>
                    <span style={{ fontSize: 11, fontWeight: 600, color: "var(--blue)" }}>
                      {s.source || "Unknown source"}
                    </span>
                    <span style={{ fontSize: 10, color: "var(--text-dim)" }}>·</span>
                    <span style={{ fontSize: 11, color: "var(--text-dim)" }}>
                      {fmtDateTime(s.collected_at)}
                    </span>
                    <span style={{
                      fontSize: 10, fontWeight: 700, padding: "1px 6px", borderRadius: 4,
                      background: `${catColor}14`, color: catColor, marginLeft: "auto",
                    }}>
                      {s.relevance_score}/10
                    </span>
                  </div>
                  <p style={{ fontSize: 12, color: "var(--text-muted)", margin: "0 0 4px", lineHeight: 1.5 }}>
                    "{s.snippet}"
                  </p>
                  {s.source_url && !s.source_url.startsWith("playstore://") && (
                    <a
                      href={s.source_url}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        display: "inline-flex", alignItems: "center", gap: 4,
                        fontSize: 11, fontWeight: 600, color: "var(--blue)", textDecoration: "none",
                      }}
                    >
                      <ExternalLink size={10} /> View source
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
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
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────── */
export default function Dashboard() {
  const [stats, setStats]       = useState(null);
  const [brief, setBrief]       = useState(null);
  const [patterns, setPatterns] = useState([]);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([api.signalStats(), api.todayBrief(), api.topPatterns(8)])
      .then(([s, b, p]) => { setStats(s); setBrief(b); setPatterns(p); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <DashboardSkeleton />;

  const today = new Date().toLocaleDateString("en-IN", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });

  const b = brief?.brief;
  const allBriefItems = [
    ...(b?.pain_pulse || []).map(i => ({ ...i, _stream: "pain_pulse" })),
    ...(b?.competitor_move || []).map(i => ({ ...i, _stream: "competitor_move" })),
    ...(b?.opportunity || []).map(i => ({ ...i, _stream: "opportunity" })),
  ];
  const hasBrief = allBriefItems.length > 0;

  return (
    <div className="animate-fade-in">

      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 36 }}>
        <div>
          <p className="section-label">Overview</p>
          <h2 style={{
            fontFamily: "'Montserrat Alternates', sans-serif",
            fontSize: 28, fontWeight: 800, color: "var(--text)",
            letterSpacing: "-1.2px", margin: "0 0 8px",
          }}>
            Dashboard
          </h2>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Clock size={12} style={{ color: "var(--text-dim)" }} />
            <span style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 500 }}>{today}</span>
          </div>
        </div>
        <div style={{
          display: "flex", alignItems: "center", gap: 7, padding: "7px 14px", borderRadius: 99,
          background: "var(--green-tint)", border: "1px solid var(--green-border)",
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

      {/* Brief — compact */}
      <div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div>
            <p className="section-label">Intelligence</p>
            <h2 style={{
              fontFamily: "'Montserrat Alternates', sans-serif",
              fontSize: 20, fontWeight: 800, color: "var(--text)", letterSpacing: "-.6px", margin: 0,
            }}>
              Today's Brief
            </h2>
          </div>
          {hasBrief ? (
            <span style={{
              display: "flex", alignItems: "center", gap: 5,
              fontSize: 11, fontWeight: 700, padding: "6px 14px", borderRadius: 99,
              background: "var(--green-tint)", color: "var(--green)",
              border: "1px solid var(--green-border)", textTransform: "uppercase", letterSpacing: ".5px",
            }}>
              <ArrowUpRight size={11} /> Generated
            </span>
          ) : (
            <span style={{
              fontSize: 11, fontWeight: 600, padding: "6px 14px", borderRadius: 99,
              background: "var(--blue-tint)", color: "var(--text-dim)", border: "1px solid var(--border-card)",
            }}>
              Not generated yet
            </span>
          )}
        </div>

        {hasBrief ? (
          <div className="glass-card" style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
            <BriefStream title="Pain Pulse"      dotColor="#EF4444" items={b.pain_pulse}      accentColor="#EF4444" />
            <BriefStream title="Competitor Move" dotColor="#1889F6" items={b.competitor_move} accentColor="#1889F6" />
            <BriefStream title="Opportunity"     dotColor="#22C55E" items={b.opportunity}     accentColor="#22C55E" />
          </div>
        ) : (
          <div className="glass-card" style={{ padding: "36px 32px", textAlign: "center" }}>
            <p style={{ fontSize: 13, fontStyle: "italic", color: "var(--text-dim)", margin: 0 }}>
              Brief is generated daily at 5:30 AM IST. Run{" "}
              <code style={{ color: "var(--blue)", fontFamily: "monospace", fontSize: 12 }}>POST /trigger/brief</code> to generate now.
            </p>
          </div>
        )}
      </div>

      {/* Patterns — expandable with sources */}
      {patterns.length > 0 && (
        <>
          <div className="divider" style={{ margin: "36px 0" }} />
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
              <div>
                <p className="section-label">Patterns</p>
                <h2 style={{
                  fontFamily: "'Montserrat Alternates', sans-serif",
                  fontSize: 20, fontWeight: 800, color: "var(--text)", letterSpacing: "-.6px", margin: 0,
                }}>
                  Recurring Themes
                </h2>
              </div>
              <div style={{
                display: "flex", alignItems: "center", gap: 6, padding: "6px 14px", borderRadius: 99,
                background: "var(--blue-tint)", border: "1px solid rgba(24,137,246,.18)",
              }}>
                <Layers size={11} style={{ color: "var(--blue)" }} />
                <span style={{ fontSize: 11, fontWeight: 700, color: "var(--blue)", textTransform: "uppercase", letterSpacing: ".5px" }}>
                  {patterns.length} active
                </span>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {patterns.map(p => <PatternCard key={p.id} pattern={p} />)}
            </div>
          </div>
        </>
      )}

    </div>
  );
}
