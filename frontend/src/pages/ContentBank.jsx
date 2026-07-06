import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { FileEdit, Check, X, Copy, Pencil, ChevronDown, CheckCheck } from "lucide-react";
import {
  AUDIENCES, FORMATS, STATUSES, FORMAT_COLOR, STATUS_COLOR, FORMAT_LABEL,
  fmtDate, fmtDayShort, Pill, FilterRow, Receipt, btnStyle,
} from "../components/contentBankShared";
import PlatformPreview from "../components/PlatformPreview";
import SaveButton from "../components/SaveButton";

// Order pieces read in within a day's calendar view — short formats first,
// long-form last, matching how the generator writes them (short kit, long kit).
const FORMAT_ORDER = ["linkedin", "instagram_post", "instagram_reel", "whatsapp", "linkedin_article", "email", "blog"];

function isoDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

const VIEWS = [
  { value: "calendar", label: "Calendar" },
  { value: "list",     label: "List" },
];

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
        <Pill color={color}>{FORMAT_LABEL[item.format] || item.format}</Pill>
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
        <SaveButton
          itemType="content_piece"
          itemId={item.id}
          title={`${item.format} for ${item.audience}`}
          content={item}
        />
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
            <button onClick={() => setStatus("rejected")} style={btnStyle("#EF4444")}><X size={12} /> Decline</button>
            <button onClick={() => setStatus("posted")} style={btnStyle("#1889F6")}><CheckCheck size={12} /> Posted</button>
            <button onClick={copyBody} style={btnStyle("#94A3B8")}><Copy size={12} /> {copied ? "Copied!" : "Copy"}</button>
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

function CalendarView() {
  const days = useMemo(() => Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() + i);
    return d;
  }), []);

  const [items, setItems] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(isoDate(days[0]));

  useEffect(() => {
    setLoading(true);
    api.contentPieces({ scheduled_date_from: isoDate(days[0]), scheduled_date_to: isoDate(days[6]) }, 200, 0)
      .then(setItems)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [days]);

  function handleUpdated(id, patch) {
    setItems(prev => prev.map(it => it.id === id ? { ...it, ...patch } : it));
  }

  const byDay = useMemo(() => {
    const map = {};
    for (const it of items || []) {
      const key = it.scheduled_date;
      if (!map[key]) map[key] = [];
      map[key].push(it);
    }
    return map;
  }, [items]);

  const selectedItems = (byDay[selected] || []).slice().sort(
    (a, b) => FORMAT_ORDER.indexOf(a.format) - FORMAT_ORDER.indexOf(b.format)
  );

  return (
    <div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 24 }}>
        {days.map(d => {
          const key = isoDate(d);
          const dayItems = byDay[key] || [];
          const hasContent = dayItems.length > 0;
          const audience = dayItems[0]?.audience;
          const patternName = dayItems[0]?.pattern_name;
          const isActive = selected === key;

          return (
            <button
              key={key}
              onClick={() => setSelected(key)}
              style={{
                textAlign: "left", minWidth: 150, padding: "12px 14px", borderRadius: 12, cursor: "pointer",
                border: isActive ? "1px solid rgba(24,137,246,.4)" : "1px solid var(--border-card)",
                background: isActive ? "var(--blue-tint)" : "rgba(255,255,255,.015)",
              }}
            >
              <p style={{ fontSize: 11, fontWeight: 700, color: isActive ? "var(--blue)" : "var(--text-muted)", margin: "0 0 6px", textTransform: "uppercase", letterSpacing: ".4px" }}>
                {fmtDayShort(d)}
              </p>
              {loading ? (
                <div className="shimmer" style={{ height: 14, borderRadius: 6, width: "80%" }} />
              ) : hasContent ? (
                <>
                  <p style={{ fontSize: 12, fontWeight: 600, color: "var(--text)", margin: "0 0 6px",
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {patternName || "—"}
                  </p>
                  <Pill color={audience === "supplier" ? "#F59E0B" : "#1889F6"}>{audience}</Pill>
                </>
              ) : (
                <p style={{ fontSize: 11, color: "var(--text-dim)", fontStyle: "italic", margin: 0 }}>No content yet</p>
              )}
            </button>
          );
        })}
      </div>

      {loading ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: 14 }}>
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="shimmer" style={{ height: 220, borderRadius: 14 }} />
          ))}
        </div>
      ) : selectedItems.length === 0 ? (
        <div className="glass-card" style={{ padding: "64px 20px", textAlign: "center" }}>
          <FileEdit size={32} style={{ color: "var(--text-dim)", margin: "0 auto 12px", display: "block" }} />
          <p style={{ color: "var(--text-dim)", fontSize: 13, fontStyle: "italic", margin: 0 }}>
            No content scheduled for this day yet. The Content Generator tops up the calendar daily at 5:45 AM IST.
          </p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: 14 }}>
          {selectedItems.map(item => (
            <PlatformPreview key={item.id} item={item} onUpdated={handleUpdated} />
          ))}
        </div>
      )}
    </div>
  );
}

function ListView() {
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
    <div>
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

export default function ContentBank() {
  const [view, setView] = useState("calendar");

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
          One topic a day, repurposed across every platform — review, edit, approve
        </p>
      </div>

      <div style={{ marginBottom: 24 }}>
        <FilterRow options={VIEWS} value={view} onChange={setView} />
      </div>

      {view === "calendar" ? <CalendarView /> : <ListView />}
    </div>
  );
}
