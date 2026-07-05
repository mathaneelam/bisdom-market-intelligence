import { ExternalLink } from "lucide-react";

export const AUDIENCES = [
  { value: "",         label: "All" },
  { value: "buyer",    label: "Buyer" },
  { value: "supplier", label: "Supplier" },
];

export const FORMATS = [
  { value: "",                 label: "All" },
  { value: "linkedin",         label: "LinkedIn Post" },
  { value: "linkedin_article", label: "LinkedIn Article" },
  { value: "instagram_post",   label: "Instagram Post" },
  { value: "instagram_reel",   label: "Instagram Reel" },
  { value: "whatsapp",         label: "WhatsApp" },
  { value: "email",            label: "Email" },
  { value: "blog",             label: "Blog" },
];

export const STATUSES = [
  { value: "draft",    label: "Draft" },
  { value: "approved", label: "Approved" },
  { value: "posted",   label: "Posted" },
  { value: "rejected", label: "Rejected" },
  { value: "",         label: "All" },
];

export const FORMAT_COLOR = {
  linkedin: "#1889F6", linkedin_article: "#1889F6",
  instagram_post: "#EC4899", instagram_reel: "#EC4899",
  blog: "#22C55E", whatsapp: "#F59E0B", email: "#06B6D4",
};

export const STATUS_COLOR = {
  draft: "#94A3B8", approved: "#22C55E", posted: "#1889F6", rejected: "#EF4444",
};

export const FORMAT_LABEL = Object.fromEntries(FORMATS.filter(f => f.value).map(f => [f.value, f.label]));

export function fmtDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export function fmtDayShort(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" });
}

export const formatUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("playstore://")) {
    const pkg = url.replace("playstore://", "").split("/")[0];
    return `https://play.google.com/store/apps/details?id=${pkg}`;
  }
  return url;
};

export function Pill({ children, color }) {
  return (
    <span style={{
      fontSize: 11, fontWeight: 700,
      padding: "3px 10px", borderRadius: 99,
      background: `${color}14`, color, border: `1px solid ${color}28`,
      whiteSpace: "nowrap", letterSpacing: ".3px",
    }}>
      {children}
    </span>
  );
}

export function FilterRow({ options, value, onChange }) {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {options.map(({ value: v, label }) => {
        const isActive = value === v;
        return (
          <button
            key={v || "all"}
            onClick={() => onChange(v)}
            style={{
              padding: "6px 15px", borderRadius: 99,
              fontSize: 12, fontWeight: 600, cursor: "pointer", transition: "all .2s",
              border: isActive ? "1px solid rgba(24,137,246,.35)" : "1px solid var(--border-card)",
              background: isActive ? "var(--blue-tint)" : "transparent",
              color: isActive ? "var(--blue)" : "var(--text-muted)",
            }}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}

export function Receipt({ r }) {
  return (
    <div style={{ padding: "10px 14px", borderRadius: 8, background: "rgba(255,255,255,.02)", border: "1px solid var(--border-card)" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)" }}>
          {r.source} {r.author ? `· ${r.author}` : ""}
        </span>
        <span style={{ fontSize: 11, color: "var(--text-dim)" }}>{fmtDate(r.collected_at)}</span>
      </div>
      <p style={{ fontSize: 12, color: "var(--text)", margin: "0 0 6px", lineHeight: 1.5 }}>
        "{r.snippet}"
      </p>
      {r.source_url && (
        <a href={formatUrl(r.source_url)} target="_blank" rel="noopener noreferrer"
          style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11, color: "var(--blue)", textDecoration: "none" }}>
          View original <ExternalLink size={11} />
        </a>
      )}
    </div>
  );
}

export function btnStyle(color) {
  return {
    display: "inline-flex", alignItems: "center", gap: 6,
    padding: "7px 14px", borderRadius: 8, fontSize: 12, fontWeight: 700,
    border: `1px solid ${color}30`, background: `${color}14`, color,
    cursor: "pointer",
  };
}
