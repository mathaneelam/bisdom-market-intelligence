import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { AlertCircle, TrendingUp, Zap, BarChart2, ArrowUpRight, Clock } from "lucide-react";

function StatCard({ icon: Icon, label, value, gradient, iconBg, delay }) {
  return (
    <div
      className={`glass-card p-6 animate-fade-in animate-fade-in-delay-${delay}`}
      style={{ overflow: 'hidden', position: 'relative' }}
    >
      {/* Decorative gradient blob */}
      <div style={{
        position: 'absolute',
        top: '-20px',
        right: '-20px',
        width: '80px',
        height: '80px',
        background: gradient,
        borderRadius: '50%',
        opacity: 0.15,
        filter: 'blur(20px)',
      }} />
      <div className="flex items-center gap-3 mb-4 relative">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{
          background: iconBg,
          boxShadow: `0 4px 12px ${iconBg}33`,
        }}>
          <Icon size={18} className="text-white" />
        </div>
        <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#94a3b8' }}>{label}</p>
      </div>
      <p className="text-4xl font-extrabold relative" style={{ color: '#1e293b', letterSpacing: '-0.02em' }}>
        {value ?? <span className="shimmer inline-block w-12 h-8"></span>}
      </p>
    </div>
  );
}

function BriefSection({ title, emoji, items, accentColor, borderColor }) {
  if (!items || items.length === 0)
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold mb-3" style={{ color: '#64748b' }}>{emoji} {title}</h3>
        <p className="text-sm italic" style={{ color: '#cbd5e1' }}>No signals above threshold yet.</p>
      </div>
    );
  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-bold mb-4" style={{ color: '#334155' }}>{emoji} {title}</h3>
      <ul className="space-y-3">
        {items.map((s, i) => (
          <li
            key={i}
            className="p-4 rounded-xl transition-all duration-200"
            style={{
              background: 'rgba(255, 255, 255, 0.6)',
              borderLeft: `3px solid ${borderColor}`,
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.03)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateX(4px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.06)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateX(0)';
              e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.03)';
            }}
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <p className="text-sm font-semibold leading-snug" style={{ color: '#1e293b' }}>{s.summary}</p>
              <span className="text-xs font-bold px-2.5 py-1 rounded-lg shrink-0" style={{
                background: `${accentColor}15`,
                color: accentColor,
              }}>
                {s.relevance_score}/10
              </span>
            </div>
            <p className="text-xs leading-relaxed" style={{ color: '#64748b' }}>{s.insight}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats]   = useState(null);
  const [brief, setBrief]   = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.signalStats(), api.todayBrief()])
      .then(([s, b]) => { setStats(s); setBrief(b); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="space-y-6">
      <div className="shimmer h-8 w-48"></div>
      <div className="grid grid-cols-4 gap-5">
        {[1,2,3,4].map(i => <div key={i} className="shimmer h-32 rounded-2xl"></div>)}
      </div>
      <div className="shimmer h-64 rounded-2xl"></div>
    </div>
  );

  const today = new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

  return (
    <div>
      {/* Header */}
      <div className="mb-8 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-extrabold" style={{ color: '#0f172a', letterSpacing: '-0.02em' }}>Dashboard</h2>
            <div className="flex items-center gap-2 mt-1.5">
              <Clock size={13} style={{ color: '#94a3b8' }} />
              <p className="text-sm font-medium" style={{ color: '#94a3b8' }}>{today}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-full" style={{
            background: 'rgba(34, 197, 94, 0.08)',
            border: '1px solid rgba(34, 197, 94, 0.15)',
          }}>
            <div className="w-2 h-2 rounded-full pulse-dot" style={{ background: '#22c55e' }}></div>
            <span className="text-xs font-semibold" style={{ color: '#16a34a' }}>Live</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-5 mb-8">
        <StatCard icon={BarChart2}   label="Total Signals"    value={stats?.total}              gradient="#6366f1" iconBg="#6366f1" delay={1} />
        <StatCard icon={AlertCircle} label="Pain Pulse"       value={stats?.pain_pulse}          gradient="#ef4444" iconBg="#ef4444" delay={2} />
        <StatCard icon={TrendingUp}  label="Competitor Move"  value={stats?.competitor_move}     gradient="#3b82f6" iconBg="#3b82f6" delay={3} />
        <StatCard icon={Zap}         label="Opportunity"      value={stats?.opportunity_signal}  gradient="#22c55e" iconBg="#22c55e" delay={4} />
      </div>

      {/* Today's Brief */}
      <div className="animate-fade-in" style={{ animationDelay: '0.3s', opacity: 0 }}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold" style={{ color: '#0f172a' }}>Today's Intelligence Brief</h2>
          {brief?.brief ? (
            <span className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full" style={{
              background: 'rgba(34, 197, 94, 0.08)',
              color: '#16a34a',
              border: '1px solid rgba(34, 197, 94, 0.15)',
            }}>
              <ArrowUpRight size={12} />
              Generated
            </span>
          ) : (
            <span className="text-xs font-medium px-3 py-1.5 rounded-full" style={{
              background: '#f1f5f9',
              color: '#94a3b8',
            }}>
              Not generated yet
            </span>
          )}
        </div>

        {brief?.brief ? (
          <div className="grid grid-cols-3 gap-5">
            <BriefSection title="Pain Pulse"       emoji="🔴" items={brief.brief.pain_pulse}       accentColor="#ef4444" borderColor="#fca5a5" />
            <BriefSection title="Competitor Move"  emoji="🔵" items={brief.brief.competitor_move}  accentColor="#3b82f6" borderColor="#93c5fd" />
            <BriefSection title="Opportunity"      emoji="🟢" items={brief.brief.opportunity}      accentColor="#22c55e" borderColor="#86efac" />
          </div>
        ) : (
          <div className="glass-card p-8 text-center">
            <p className="text-sm italic" style={{ color: '#94a3b8' }}>
              The brief is generated daily at 5:30 AM IST after AI processing runs. Collect signals and run the processor to generate one.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
