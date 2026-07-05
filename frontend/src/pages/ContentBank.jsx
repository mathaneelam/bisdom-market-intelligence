import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { FileEdit, ExternalLink, Check, X, Copy, Pencil, ChevronDown } from "lucide-react";

const AUDIENCES = [
  { value: "",         label: "All" },
  { value: "buyer",    label: "Buyer" },
  { value: "supplier", label: "Supplier" },
];

const FORMATS = [
  { value: "",          label: "All" },
  { value: "linkedin",  label: "LinkedIn" },
  { value: "instagram", label: "Instagram" },
  { value: "blog",      label: "Blog" },
  { value: "ad",        label: "Ad" },
  { value: "email",     label: "Email/WhatsApp" },
];

const STATUSES = [
  { value: "draft",    label: "Draft" },
  { value: "approved", label: "Approved" },
  { value: "posted",   label: "Posted" },
  { value: "rejected", label: "Rejected" },
  { value: "",         label: "All" },
];

const FORMAT_COLOR = {
  linkedin: "#1889F6", instagram: "#EC4899", blog: "#22C55E",
  ad: "#F59E0B", email: "#06B6D4",
};

const STATUS_COLOR = {
  draft: "#94A3B8", approved: "#22C55E", posted: "#1889F6", rejected: "#EF4444",
};

function fmtDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

const formatUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("playstore://")) {
    const pkg = url.replace("playstore://", "").split("/")[0];
    return `https://play.google.com/store/apps/details?id=${pkg}`;
  }
  return url;
};

function Pill({ children, color }) {
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

function FilterRow({ options, value, onChange }) {
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

function Receipt({ r }) {
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

function ContentCard({ item, onUpdated }) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState(null);
  const [editing, setEditing] = useState(false);
  const [draftBody, setDraftBody] = useState(item.body);
  const [copied, setCopied] = useState(false);
  const color = FORMAT_COLOR[item.format] || "#1889F6";

  useEffect(() => {
    if (open && !detail) {
      api.contentPiece(item.id).then(setDetail).catch(console.error);
    }
  }, [open]);

  async function setStatus(status) {
    await api.updateContentPiece(item.id, { status });
    onUpdated(item.id, { status });
  }

  async function saveEdit() {
    await api.updateContentPiece(item.id, { body: draftBody });
    onUpdated(item.id, { body: draftBody });
    setEditing(false);
    setDetail(d => d ? { ...d, body: draftBody } : d);
  }

  function copyBody() {
    navigator.clipboard.writeText(draftBody);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
      <div
        onClick={() => setOpen(!open)}
        style={{ padding: "16px 20px", cursor: "pointer", display: "flex", alignItems: "center", gap: 12 }}
      >
        <Pill color={color}>{item.format}</Pill>
        <Pill color="#94A3B8">{item.audience}</Pill>
        <Pill color={item.tone === "contrast" ? "#F59E0B" : "#1889F6"}>
          {item.tone === "contrast" ? "Direct" : "Educational"}
        </Pill>
        <p style={{ flex: 1, margin: 0, fontSize: 13, fontWeight: 600, color: "var(--text)",
          overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {item.pattern_name || "—"}
        </p>
        <Pill color={STATUS_COLOR[item.status] || "#94A3B8"}>{item.status}</Pill>
        <span style={{ fontSize: 11, color: "var(--text-dim)", whiteSpace: "nowrap" }}>{fmtDate(item.created_at)}</span>
        <ChevronDown size={14} style={{
          color: "var(--text-dim)", transform: open ? "rotate(180deg)" : "rotate(0)", transition: "transform .2s",
        }} />
      </div>

      {open && (
        <div style={{ padding: "0 20px 20px", borderTop: "1px solid var(--border-card)" }}>
          <div style={{ paddingTop: 16 }}>
            {editing ? (
              <textarea
                value={draftBody}
                onChange={e => setDraftBody(e.target.value)}
                rows={8}
                style={{
                  width: "100%", fontSize: 13, lineHeight: 1.6, color: "var(--text)",
                  background: "rgba(255,255,255,.02)", border: "1px solid var(--border-card)",
                  borderRadius: 10, padding: 14, resize: "vertical", fontFamily: "inherit",
                }}
              />
            ) : (
              <p style={{ fontSize: 13, lineHeight: 1.65, color: "var(--text)", whiteSpace: "pre-wrap", margin: 0 }}>
                {draftBody}
              </p>
            )}
          </div>

          <div style={{ display: "flex", gap: 8, marginTop: 14, flexWrap: "wrap" }}>
            {editing ? (
              <button onClick={saveEdit} style={btnStyle("#22C55E")}>Save</button>
            ) : (
              <button onClick={() => setEditing(true)} style={btnStyle("#94A3B8")}><Pencil size={12} /> Edit</button>
            )}
            <button onClick={() => setStatus("approved")} style={btnStyle("#22C55E")}><Check size={12} /> Approve</button>
            <button onClick={() => setStatus("rejected")} style={btnStyle("#EF4444")}><X size={12} /> Reject</button>
            <button onClick={copyBody} style={btnStyle("#1889F6")}><Copy size={12} /> {copied ? "Copied!" : "Copy"}</button>
          </div>

          <div style={{ marginTop: 18 }}>
            <p className="section-label" style={{ margin: "0 0 10px" }}>Based on these reviews</p>
            {!detail ? (
              <div className="shimmer" style={{ height: 40, borderRadius: 8 }} />
            ) : detail.receipts.length === 0 ? (
              <p style={{ fontSize: 12, color: "var(--text-dim)", fontStyle: "italic" }}>No receipts on file for this piece.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {detail.receipts.map(r => <Receipt key={r.id} r={r} />)}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function btnStyle(color) {
  return {
    display: "inline-flex", alignItems: "center", gap: 6,
    padding: "7px 14px", borderRadius: 8, fontSize: 12, fontWeight: 700,
    border: `1px solid ${color}30`, background: `${color}14`, color,
    cursor: "pointer",
  };
}

export default function ContentBank() {
  const [audience, setAudience] = useState("");
  const [format, setFormat]     = useState("");
  const [status, setStatus]     = useState("draft");
  const [items, setItems]       = useState(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    setLoading(true);
    api.contentPieces({ audience, format, status })
      .then(setItems)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [audience, format, status]);

  function handleUpdated(id, patch) {
    setItems(prev => prev.map(it => it.id === id ? { ...it, ...patch } : it));
  }

  return (
    <div className="animate-fade-in">
      <div style={{ marginBottom: 28 }}>
        <p className="section-label">Marketing</p>
        <h2 style={{
          fontFamily: "'Montserrat Alternates', sans-serif",
          fontSize: 28, fontWeight: 800, color: "var(--text)", letterSpacing: "-1.2px",
          margin: "0 0 6px",
        }}>
          Content Bank
        </h2>
        <p style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 500, margin: 0 }}>
          Marketing content generated from real competitor pain signals — review, edit, approve
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 24 }}>
        <FilterRow options={STATUSES} value={status} onChange={setStatus} />
        <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
          <FilterRow options={AUDIENCES} value={audience} onChange={setAudience} />
          <FilterRow options={FORMATS} value={format} onChange={setFormat} />
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="shimmer" style={{ height: 56, borderRadius: 14 }} />
          ))
        ) : items.length === 0 ? (
          <div className="glass-card" style={{ padding: "64px 20px", textAlign: "center" }}>
            <FileEdit size={32} style={{ color: "var(--text-dim)", margin: "0 auto 12px", display: "block" }} />
            <p style={{ color: "var(--text-dim)", fontSize: 13, fontStyle: "italic", margin: 0 }}>
              No content pieces here yet. The Content Generator runs daily at 5:45 AM IST.
            </p>
          </div>
        ) : items.map(item => (
          <ContentCard key={item.id} item={item} onUpdated={handleUpdated} />
        ))}
      </div>
    </div>
  );
}
