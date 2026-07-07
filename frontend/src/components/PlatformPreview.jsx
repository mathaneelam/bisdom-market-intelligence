import { useEffect, useState } from "react";
import {
  ThumbsUp, MessageCircle, Repeat2, Send, Heart, Bookmark, CornerDownRight,
  Image as ImageIcon, Check, X, Copy, Pencil, ChevronDown, CheckCheck, Loader2, RefreshCw,
} from "lucide-react";
import { api } from "../lib/api";
import { Pill, Receipt, btnStyle, FORMAT_COLOR, FORMAT_LABEL, STATUS_COLOR } from "./contentBankShared";
import SaveButton from "./SaveButton";

function ImageBrief({ text, imageUrl, itemId, onUpdated, square, tall }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!text && !imageUrl) return null;

  // Match the box shape to what the backend generated for this platform:
  // reels are tall (9/16), Instagram posts square, everything else wide (16/9).
  const boxAspect = tall ? "9 / 16" : square ? "1 / 1" : "16 / 9";
  const boxMaxWidth = tall ? 260 : undefined;   // keep a reel preview phone-sized

  async function generateImage(e) {
    e.stopPropagation();
    setLoading(true);
    setError(null);
    try {
      const data = await api.generateContentPieceImage(itemId);
      if (onUpdated) {
        onUpdated(itemId, { image_url: data.image_url });
      }
    } catch (err) {
      console.error(err);
      setError("Image generation failed. The free service may be busy — try again.");
    } finally {
      setLoading(false);
    }
  }

  if (imageUrl) {
    const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
    // Bust the browser cache with a fresh param each regenerate, otherwise the
    // <img> keeps showing the old bytes even though the DB row changed.
    const src = (imageUrl.startsWith("http") ? imageUrl : `${BASE}${imageUrl}`) + `?v=${loading ? "loading" : Date.now()}`;
    return (
      <div className="animate-fade-in" style={{
        position: "relative", width: "100%", maxWidth: boxMaxWidth, aspectRatio: boxAspect,
        overflow: "hidden", borderRadius: 10, border: "1px solid var(--border-card)",
        background: "#000", margin: tall ? "10px auto 0" : "10px 0 0"
      }}>
        <img
          src={src}
          alt="AI Generated visual"
          style={{ width: "100%", height: "100%", objectFit: "cover", opacity: loading ? 0.4 : 1, transition: "opacity 0.2s" }}
        />
        <button
          onClick={generateImage}
          disabled={loading}
          title="Regenerate image"
          style={{
            position: "absolute", top: 8, right: 8, display: "flex", alignItems: "center", gap: 5,
            background: "rgba(0,0,0,0.6)", color: "#fff", border: "none", borderRadius: 6,
            padding: "5px 9px", fontSize: 10, fontWeight: 600, cursor: loading ? "default" : "pointer",
            backdropFilter: "blur(4px)", opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? <Loader2 size={11} className="animate-spin" /> : <RefreshCw size={11} />}
          {loading ? "Generating..." : "Regenerate"}
        </button>
        <span style={{
          position: "absolute", bottom: 8, right: 8, fontSize: 9,
          color: "rgba(255,255,255,0.7)", background: "rgba(0,0,0,0.6)",
          padding: "3px 6px", borderRadius: 4, backdropFilter: "blur(4px)",
          letterSpacing: "0.5px", pointerEvents: "none"
        }}>
          AI Generated
        </span>
        {error && (
          <p style={{
            position: "absolute", bottom: 8, left: 8, right: 8, margin: 0,
            fontSize: 10, color: "#fff", background: "rgba(239,68,68,0.85)",
            padding: "4px 7px", borderRadius: 4,
          }}>{error}</p>
        )}
      </div>
    );
  }

  return (
    <div style={{
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      gap: 10, textAlign: "center", padding: "20px 16px",
      border: "1px dashed var(--border-card)", borderRadius: 10,
      background: "rgba(255,255,255,.02)", width: "100%", maxWidth: boxMaxWidth, boxSizing: "border-box",
      aspectRatio: (square || tall) ? boxAspect : undefined,
      minHeight: (square || tall) ? undefined : 110,
      margin: tall ? "10px auto 0" : "10px 0 0"
    }}>
      <ImageIcon size={16} style={{ color: "var(--text-dim)" }} />
      <p style={{ fontSize: 11, color: "var(--text-dim)", fontStyle: "italic", margin: 0, lineHeight: 1.5, maxWidth: 320 }}>
        {text}
      </p>
      {error && (
        <p style={{ fontSize: 10, color: "#EF4444", margin: 0 }}>{error}</p>
      )}
      <button
        onClick={generateImage}
        disabled={loading}
        style={{
          background: "linear-gradient(135deg, #1889F6, #0A5FC2)",
          color: "#fff", border: "none", borderRadius: 6,
          padding: "6px 12px", fontSize: 11, fontWeight: 600,
          cursor: "pointer", display: "flex", alignItems: "center", gap: 6,
          opacity: loading ? 0.7 : 1, transition: "opacity 0.2s"
        }}
      >
        {loading ? (
          <>
            <Loader2 size={12} className="animate-spin" />
            Generating...
          </>
        ) : (
          "Generate AI Image"
        )}
      </button>
    </div>
  );
}

function Avatar({ size = 32 }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%", flexShrink: 0,
      background: "linear-gradient(135deg, #1889F6, #0A5FC2)",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontSize: size * 0.4, fontWeight: 800, color: "#fff",
    }}>
      B
    </div>
  );
}

function IconRow({ icons }) {
  return (
    <div style={{ display: "flex", gap: 18, padding: "10px 0", borderTop: "1px solid var(--border-card)", marginTop: 12 }}>
      {icons.map(({ Icon, label }, i) => (
        <span key={i} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: "var(--text-dim)" }}>
          <Icon size={15} /> {label}
        </span>
      ))}
    </div>
  );
}

function CommentStrip({ text }) {
  if (!text) return null;
  return (
    <div style={{ display: "flex", gap: 8, marginTop: 10, paddingTop: 10, borderTop: "1px solid var(--border-card)" }}>
      <CornerDownRight size={13} style={{ color: "var(--text-dim)", marginTop: 3, flexShrink: 0 }} />
      <div>
        <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-dim)", margin: "0 0 2px", textTransform: "uppercase", letterSpacing: ".4px" }}>
          First comment
        </p>
        <p style={{ fontSize: 12.5, color: "var(--text)", margin: 0, lineHeight: 1.5 }}>{text}</p>
      </div>
    </div>
  );
}

function LinkedInMock({ item, onUpdated }) {
  const isArticle = item.format === "linkedin_article";
  return (
    <div style={{ padding: 16, borderRadius: 12, border: "1px solid var(--border-card)", background: "rgba(255,255,255,.015)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
        <Avatar />
        <div>
          <p style={{ fontSize: 13, fontWeight: 700, color: "var(--text)", margin: 0 }}>Bisdom</p>
          <p style={{ fontSize: 11, color: "var(--text-dim)", margin: 0 }}>B2B Commerce Platform · Just now</p>
        </div>
      </div>
      {isArticle && item.title && (
        <p style={{ fontSize: 15, fontWeight: 800, color: "var(--text)", margin: "0 0 10px" }}>{item.title}</p>
      )}
      <ImageBrief text={item.image_brief} imageUrl={item.image_url} itemId={item.id} onUpdated={onUpdated} />
      <p style={{ fontSize: 13, lineHeight: 1.65, color: "var(--text)", whiteSpace: "pre-wrap", margin: "12px 0 0" }}>
        {item.body}
      </p>
      <IconRow icons={[
        { Icon: ThumbsUp, label: "Like" }, { Icon: MessageCircle, label: "Comment" },
        { Icon: Repeat2, label: "Repost" }, { Icon: Send, label: "Send" },
      ]} />
      <CommentStrip text={item.comment_note} />
    </div>
  );
}

function InstagramPostMock({ item, onUpdated }) {
  return (
    <div style={{ padding: 16, borderRadius: 12, border: "1px solid var(--border-card)", background: "rgba(255,255,255,.015)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
        <Avatar size={28} />
        <p style={{ fontSize: 13, fontWeight: 700, color: "var(--text)", margin: 0 }}>bisdom.official</p>
      </div>
      <ImageBrief text={item.image_brief} imageUrl={item.image_url} itemId={item.id} onUpdated={onUpdated} square />
      <IconRow icons={[
        { Icon: Heart, label: "" }, { Icon: MessageCircle, label: "" },
        { Icon: Send, label: "" }, { Icon: Bookmark, label: "" },
      ]} />
      <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text)", whiteSpace: "pre-wrap", margin: "6px 0 0" }}>
        <span style={{ fontWeight: 700 }}>bisdom.official </span>{item.body}
      </p>
      <CommentStrip text={item.comment_note} />
    </div>
  );
}

function InstagramReelMock({ item, onUpdated }) {
  const lines = item.body.split("\n").filter(Boolean);
  return (
    <div style={{ padding: 16, borderRadius: 12, border: "1px solid var(--border-card)", background: "rgba(255,255,255,.015)" }}>
      <ImageBrief text={item.image_brief} imageUrl={item.image_url} itemId={item.id} onUpdated={onUpdated} tall />
      <div style={{
        marginTop: 12, padding: "16px 14px", borderRadius: 14, background: "#0B0B0F",
        maxWidth: 260, marginLeft: "auto", marginRight: "auto",
        display: "flex", flexDirection: "column", gap: 10, minHeight: 280,
      }}>
        {lines.map((line, i) => {
          const beat = /^\d+-\d+\s*sec/i.test(line.trim());
          return (
            <p key={i} style={{
              margin: 0, fontSize: beat ? 10 : 12.5, color: beat ? "#8FA0B8" : "#fff",
              fontWeight: beat ? 700 : 500, textTransform: beat ? "uppercase" : "none",
              letterSpacing: beat ? ".4px" : "normal", lineHeight: 1.5,
            }}>
              {line}
            </p>
          );
        })}
      </div>
      <CommentStrip text={item.comment_note} />
    </div>
  );
}

function WhatsAppMock({ item, onUpdated }) {
  const lines = item.body.split("\n").filter(Boolean);
  return (
    <div style={{ padding: 16, borderRadius: 12, border: "1px solid var(--border-card)", background: "#0B141A" }}>
      <ImageBrief text={item.image_brief} imageUrl={item.image_url} itemId={item.id} onUpdated={onUpdated} />
      <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 12, alignItems: "flex-end" }}>
        {lines.map((line, i) => (
          <div key={i} style={{
            maxWidth: "80%", padding: "7px 10px", borderRadius: "10px 10px 2px 10px",
            background: "#005C4B", color: "#E9EDEF", fontSize: 12.5, lineHeight: 1.5,
          }}>
            {line}
          </div>
        ))}
        <span style={{ fontSize: 10, color: "#8696A0", display: "flex", alignItems: "center", gap: 3, marginTop: 2 }}>
          Just now <CheckCheck size={12} style={{ color: "#53BDEB" }} />
        </span>
      </div>
      <CommentStrip text={item.comment_note} />
    </div>
  );
}

function EmailMock({ item, onUpdated }) {
  return (
    <div style={{ padding: 16, borderRadius: 12, border: "1px solid var(--border-card)", background: "rgba(255,255,255,.015)" }}>
      <div style={{ paddingBottom: 10, borderBottom: "1px solid var(--border-card)", marginBottom: 12 }}>
        <p style={{ fontSize: 10, color: "var(--text-dim)", margin: "0 0 4px", textTransform: "uppercase", letterSpacing: ".4px" }}>Subject</p>
        <p style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", margin: 0 }}>{item.title || "(no subject)"}</p>
        <p style={{ fontSize: 11, color: "var(--text-dim)", margin: "6px 0 0" }}>From: Bisdom &lt;hello@bisdom.co&gt;</p>
      </div>
      <ImageBrief text={item.image_brief} imageUrl={item.image_url} itemId={item.id} onUpdated={onUpdated} />
      <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--text)", whiteSpace: "pre-wrap", margin: "12px 0 0" }}>
        {item.body}
      </p>
      <CommentStrip text={item.comment_note} />
    </div>
  );
}

function BlogMock({ item, onUpdated }) {
  return (
    <div style={{ padding: 16, borderRadius: 12, border: "1px solid var(--border-card)", background: "rgba(255,255,255,.015)" }}>
      <ImageBrief text={item.image_brief} imageUrl={item.image_url} itemId={item.id} onUpdated={onUpdated} />
      <h3 style={{ fontSize: 17, fontWeight: 800, color: "var(--text)", margin: "12px 0 10px" }}>{item.title}</h3>
      <p style={{ fontSize: 13, lineHeight: 1.75, color: "var(--text)", whiteSpace: "pre-wrap", margin: 0 }}>
        {item.body}
      </p>
      <CommentStrip text={item.comment_note} />
    </div>
  );
}

const MOCKS = {
  linkedin: LinkedInMock,
  linkedin_article: LinkedInMock,
  instagram_post: InstagramPostMock,
  instagram_reel: InstagramReelMock,
  whatsapp: WhatsAppMock,
  email: EmailMock,
  blog: BlogMock,
};

export default function PlatformPreview({ item, onUpdated }) {
  const [receiptsOpen, setReceiptsOpen] = useState(false);
  const [detail, setDetail] = useState(null);
  const [editing, setEditing] = useState(false);
  const [draftBody, setDraftBody] = useState(item.body);
  const [copied, setCopied] = useState(false);
  const color = FORMAT_COLOR[item.format] || "#1889F6";
  const Mock = MOCKS[item.format] || LinkedInMock;

  useEffect(() => {
    if (receiptsOpen && !detail) {
      api.contentPiece(item.id).then(setDetail).catch(console.error);
    }
  }, [receiptsOpen]);

  async function setStatus(status) {
    let confirmMsg = "";
    if (status === "posted") {
      confirmMsg = "Are you sure you want to mark this as Posted? This will permanently delete the generated image from the cloud database to save space.";
    } else if (status === "approved") {
      confirmMsg = "Are you sure you want to approve this content piece?";
    } else if (status === "rejected") {
      confirmMsg = "Are you sure you want to decline this content piece?";
    }

    if (confirmMsg && !window.confirm(confirmMsg)) {
      return;
    }

    await api.updateContentPiece(item.id, { status });
    onUpdated(item.id, { status });
  }

  async function saveEdit() {
    await api.updateContentPiece(item.id, { body: draftBody });
    onUpdated(item.id, { body: draftBody });
    setEditing(false);
  }

  function copyBody() {
    navigator.clipboard.writeText(draftBody);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="glass-card" style={{ padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <Pill color={color}>{FORMAT_LABEL[item.format] || item.format}</Pill>
        <Pill color={item.tone === "contrast" ? "#F59E0B" : "#1889F6"}>
          {item.tone === "contrast" ? "Direct" : "Educational"}
        </Pill>
        <span style={{ flex: 1 }} />
        <SaveButton
          itemType="content_piece"
          itemId={item.id}
          title={`${item.format} for ${item.audience}`}
          content={item}
        />
        <Pill color={STATUS_COLOR[item.status] || "#94A3B8"}>{item.status}</Pill>
      </div>

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
        <Mock item={{ ...item, body: draftBody }} onUpdated={onUpdated} />
      )}

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
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

      <div>
        <button
          onClick={() => setReceiptsOpen(o => !o)}
          style={{
            display: "flex", alignItems: "center", gap: 6, background: "none", border: "none",
            cursor: "pointer", padding: 0, fontSize: 11, fontWeight: 700, color: "var(--text-dim)",
            textTransform: "uppercase", letterSpacing: ".4px",
          }}
        >
          Based on these reviews
          <ChevronDown size={12} style={{ transform: receiptsOpen ? "rotate(180deg)" : "rotate(0)", transition: "transform .2s" }} />
        </button>
        {receiptsOpen && (
          !detail ? (
            <div className="shimmer" style={{ height: 40, borderRadius: 8, marginTop: 8 }} />
          ) : detail.receipts.length === 0 ? (
            <p style={{ fontSize: 12, color: "var(--text-dim)", fontStyle: "italic", marginTop: 8 }}>No receipts on file for this piece.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
              {detail.receipts.map(r => <Receipt key={r.id} r={r} />)}
            </div>
          )
        )}
      </div>
    </div>
  );
}
