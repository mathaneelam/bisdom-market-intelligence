import { NavLink, useLocation } from "react-router-dom";
import { LayoutDashboard, Radio, Users, Calendar, Globe, FileEdit } from "lucide-react";

const nav = [
  { to: "/",             label: "Dashboard",    icon: LayoutDashboard },
  { to: "/signals",      label: "Signals",      icon: Radio           },
  { to: "/sources",      label: "Sources",      icon: Globe           },
  { to: "/competitors",  label: "Competitors",  icon: Users           },
  { to: "/trade-shows",  label: "Trade Shows",  icon: Calendar        },
  { to: "/content-bank", label: "Content Bank", icon: FileEdit        },
];

const SIDEBAR_W = 240;

export default function Layout({ children }) {
  const location = useLocation();

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>


      {/* ── Sidebar ──────────────────────────────────── */}
      <aside style={{
        width: SIDEBAR_W,
        position: "fixed",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        background: "var(--nav-bg)",
        backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)",
        borderRight: "1px solid var(--border-card)",
        zIndex: 100,
      }}>

        {/* Logo */}
        <div style={{
          padding: "28px 24px 22px",
          borderBottom: "1px solid var(--border-card)",
        }}>
          <span style={{
            fontFamily: "'Montserrat Alternates', sans-serif",
            fontWeight: 800,
            fontSize: 22,
            letterSpacing: "-.5px",
            display: "block",
          }}>
            <span style={{ color: "var(--text)" }}>Bis</span>
            <span style={{ color: "var(--blue)" }}>dom</span>
          </span>
          <p style={{
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: "2px",
            textTransform: "uppercase",
            color: "var(--text-dim)",
            margin: "5px 0 0",
          }}>
            Intelligence Engine
          </p>
        </div>

        {/* Navigation */}
        <nav style={{
          flex: 1,
          padding: "14px 12px",
          display: "flex",
          flexDirection: "column",
          gap: 2,
        }}>
          {nav.map(({ to, label, icon: Icon }) => {
            const isActive =
              location.pathname === to ||
              (to !== "/" && location.pathname.startsWith(to));

            return (
              <NavLink
                key={to}
                to={to}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 11,
                  padding: "10px 14px",
                  borderRadius: 10,
                  fontSize: 13,
                  fontWeight: isActive ? 600 : 500,
                  textDecoration: "none",
                  transition: "background .2s, color .2s, border-color .2s",
                  background: isActive ? "var(--blue-tint)" : "transparent",
                  color: isActive ? "var(--blue)" : "var(--text-muted)",
                  border: isActive
                    ? "1px solid rgba(24,137,246,.22)"
                    : "1px solid transparent",
                }}
                onMouseEnter={e => {
                  if (!isActive) {
                    e.currentTarget.style.background = "rgba(255,255,255,.04)";
                    e.currentTarget.style.color = "var(--text)";
                  }
                }}
                onMouseLeave={e => {
                  if (!isActive) {
                    e.currentTarget.style.background = "transparent";
                    e.currentTarget.style.color = "var(--text-muted)";
                  }
                }}
              >
                <Icon size={16} />
                {label}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer */}
        <div style={{
          padding: "16px 24px",
          borderTop: "1px solid var(--border-card)",
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}>
          <span
            className="pulse-dot"
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: "var(--green)",
              display: "inline-block",
              flexShrink: 0,
            }}
          />
          <span style={{
            fontSize: 11,
            fontWeight: 600,
            color: "var(--text-dim)",
            letterSpacing: ".5px",
            textTransform: "uppercase",
          }}>
            Engine Active
          </span>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────── */}
      <main style={{
        marginLeft: SIDEBAR_W,
        flex: 1,
        padding: "44px 48px",
        position: "relative",
        zIndex: 1,
        minHeight: "100vh",
      }}>
        {children}
      </main>

    </div>
  );
}
