import { NavLink, useLocation } from "react-router-dom";
import { LayoutDashboard, Radio, Users, Calendar, Zap } from "lucide-react";

const nav = [
  { to: "/",            label: "Dashboard",   icon: LayoutDashboard },
  { to: "/signals",     label: "Signals",     icon: Radio           },
  { to: "/competitors", label: "Competitors", icon: Users           },
  { to: "/trade-shows", label: "Trade Shows", icon: Calendar        },
];

export default function Layout({ children }) {
  const location = useLocation();

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 fixed h-full flex flex-col" style={{
        background: 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)',
        borderRight: '1px solid rgba(226, 232, 240, 0.8)',
        boxShadow: '4px 0 24px rgba(0, 0, 0, 0.03)'
      }}>
        {/* Logo Area */}
        <div className="px-6 py-7" style={{ borderBottom: '1px solid rgba(226, 232, 240, 0.6)' }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
            }}>
              <Zap size={18} className="text-white" />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: '#94a3b8' }}>Bisdom</p>
              <h1 className="text-sm font-bold" style={{ color: '#1e293b', letterSpacing: '-0.01em' }}>Intelligence Engine</h1>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-5 space-y-1">
          {nav.map(({ to, label, icon: Icon }) => {
            const isActive = location.pathname === to || (to !== "/" && location.pathname.startsWith(to));
            return (
              <NavLink
                key={to}
                to={to}
                className="group flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
                style={isActive ? {
                  background: 'linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)',
                  color: '#4f46e5',
                  boxShadow: '0 1px 3px rgba(79, 70, 229, 0.08)',
                } : {
                  color: '#64748b',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = '#f8fafc';
                    e.currentTarget.style.color = '#334155';
                    e.currentTarget.style.transform = 'translateX(2px)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = '#64748b';
                    e.currentTarget.style.transform = 'translateX(0)';
                  }
                }}
              >
                <Icon size={18} style={{ transition: 'transform 0.2s' }} />
                {label}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-6 py-5" style={{ borderTop: '1px solid rgba(226, 232, 240, 0.6)' }}>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full pulse-dot" style={{ background: '#22c55e' }}></div>
            <p className="text-xs font-medium" style={{ color: '#94a3b8' }}>Engine Active</p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-64 flex-1 p-8 lg:p-10">
        {children}
      </main>
    </div>
  );
}
