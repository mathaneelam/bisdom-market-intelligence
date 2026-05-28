# Bisdom Market Intelligence Platform — Master Context

## What This Project Is

A standalone market intelligence platform for Bisdom — an AI-powered B2B commerce
platform targeting India's SME market in textile, garment, manufacturing, raw
materials, retail and wholesale sectors.

This platform continuously collects signals from the internet, processes them with
Claude API, and delivers a daily morning intelligence brief via Dashboard, Telegram,
WhatsApp and Email — at zero subscription cost.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI |
| Database | PostgreSQL (Supabase free tier) |
| Scheduler | APScheduler (inside FastAPI) |
| Job Queue | Redis + ARQ (Upstash free tier) |
| AI Processing | Claude API — claude-sonnet-4-6 |
| Email Delivery | Resend.com (free tier) |
| Telegram | Telegram Bot API (free) |
| WhatsApp | WhatsApp Business Cloud API (free tier) |
| Dashboard | React + TailwindCSS |
| Hosting | Railway (free tier) |
| Frontend Hosting | Vercel (free tier) |

---

## Folder Structure

```
bisdom-intelligence/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── scheduler.py
│   │
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── reddit.py
│   │   ├── google_alerts.py
│   │   ├── rss_feeds.py
│   │   ├── instagram.py
│   │   ├── linkedin.py
│   │   ├── google_trends.py
│   │   ├── play_store.py
│   │   ├── news.py
│   │   └── trade_shows.py
│   │
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── claude_processor.py
│   │   ├── scorer.py
│   │   ├── deduplicator.py
│   │   └── brief_builder.py
│   │
│   ├── delivery/
│   │   ├── __init__.py
│   │   ├── email.py
│   │   ├── telegram.py
│   │   ├── whatsapp.py
│   │   └── templates/
│   │       └── brief.html
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── signals.py
│   │   ├── briefs.py
│   │   ├── competitors.py
│   │   └── trade_shows.py
│   │
│   └── models/
│       ├── __init__.py
│       ├── signal.py
│       ├── processed_signal.py
│       ├── brief.py
│       ├── source.py
│       ├── competitor.py
│       ├── trade_show.py
│       └── keyword.py
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Signals.jsx
│       │   ├── Competitors.jsx
│       │   └── TradeShows.jsx
│       └── components/
│
├── migrations/
├── tests/
├── .env
├── docker-compose.yml
├── requirements.txt
└── CLAUDE.md
```

---

## Database Schema

```sql
CREATE TABLE signals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream          VARCHAR(50),
    source          VARCHAR(100),
    source_url      TEXT,
    raw_content     TEXT,
    author          VARCHAR(255),
    language        VARCHAR(10),
    collected_at    TIMESTAMP,
    is_processed    BOOLEAN DEFAULT FALSE,
    is_duplicate    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE processed_signals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id       UUID REFERENCES signals(id),
    summary         TEXT,
    relevance_score INTEGER,
    sentiment       VARCHAR(20),
    tags            TEXT[],
    stream          VARCHAR(50),
    insight         TEXT,
    processed_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE briefs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_date      DATE UNIQUE,
    pain_pulse      JSONB,
    competitor_move JSONB,
    opportunity     JSONB,
    full_html       TEXT,
    delivered_email BOOLEAN DEFAULT FALSE,
    delivered_tg    BOOLEAN DEFAULT FALSE,
    delivered_wa    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE competitors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100),
    website         TEXT,
    linkedin_url    TEXT,
    play_store_id   VARCHAR(255),
    rss_url         TEXT,
    is_active       BOOLEAN DEFAULT TRUE
);

CREATE TABLE trade_shows (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255),
    category        VARCHAR(100),
    city            VARCHAR(100),
    venue           TEXT,
    start_date      DATE,
    end_date        DATE,
    website         TEXT,
    relevance_note  TEXT,
    is_upcoming     BOOLEAN DEFAULT TRUE
);

CREATE TABLE keywords (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword         TEXT,
    stream          VARCHAR(50),
    language        VARCHAR(10),
    is_active       BOOLEAN DEFAULT TRUE
);
```

---

## Intelligence Streams

### Stream 1 — Pain Pulse
What buyers and suppliers are complaining about right now.

Sources: Reddit, Google Alerts, Facebook Groups (public), YouTube comments,
MouthShut, Google Play reviews, Quora, Twitter/X, Instagram, LinkedIn

### Stream 2 — Competitor Move
What competitors did this week.

Competitors to track:
- IndiaMART
- TradeIndia
- Alibaba
- Fiber2Fashion
- Textilegalaxy
- Locofast
- Fashinza
- Zilingo
- Textrade
- Baazaar.com
- Global Textile Hub
- Apparelsearch

### Stream 3 — Opportunity Signal
D2C brands and manufacturers expressing sourcing needs publicly.

Sources: Instagram hashtags, LinkedIn keyword search, IndiaMART buy leads
(public), TradeIndia buy leads (public), Reddit, funded D2C brand news

### Stream 4 — Trade Show Intelligence
Upcoming textile, garment, fashion, D2C events across India.

Key shows: Bharat Tex, Knit Show Tiruppur, IIGF Delhi, Gartex Texprocess,
DenimsandJeans India, Yarnex, F&A Show, ASF, TFI, East India Garments Fair,
India D2C Summit, India Fashion Forum, Fashion India Forum

---

## Keywords To Monitor

### Pain Pulse Keywords
- "IndiaMART fake leads"
- "B2B platform complaint India"
- "garment sourcing problem India"
- "manufacturer WhatsApp chaos"
- "textile supplier fraud India"
- "IndiaMART renewal not worth it"
- "sourcing vendor problem"

### Competitor Keywords
- "IndiaMART new feature"
- "Fiber2Fashion launch"
- "Locofast update"
- "Fashinza funding"
- "B2B textile platform India launch"

### Opportunity Keywords
- "looking for garment manufacturer India"
- "fabric supplier India MOQ"
- "clothing brand manufacturer"
- "D2C brand sourcing India"
- "knitwear manufacturer India"
- "need textile supplier"
- "recommend fabric manufacturer"

### Vernacular Keywords (Tamil/Hindi)
- "IndiaMART worth it" (Hindi/Tamil searches)
- "manufacturer dhundhna" (Hindi)
- "textile supplier problem"

---

## Collector Schedule

| Job | Cadence |
|---|---|
| Reddit + RSS + News | Every 6 hours |
| Google Trends | Daily 2AM IST |
| Instagram hashtags | Daily 2AM IST |
| Play Store reviews | Daily 2AM IST |
| AI processing | Daily 5AM IST |
| Brief builder | Daily 5:30AM IST |
| Delivery (all 3) | Daily 6AM IST |
| Trade show scraper | Weekly Sunday midnight |

---

## AI Processing — Claude System Prompt

```
You are a market intelligence analyst for Bisdom —
an AI-powered B2B commerce platform for India's
textile, garment and manufacturing SME market.

Your job is to analyse raw signals collected from
the internet and extract intelligence relevant to Bisdom.

For each signal, return ONLY valid JSON with:
- summary: one line, what this signal says
- relevance_score: 1-10 (10 = directly actionable for Bisdom)
- sentiment: positive | negative | neutral
- tags: array of relevant tags
- insight: one line explaining why this matters for Bisdom
- stream: pain_pulse | competitor_move | opportunity_signal

Only score above 7 if the signal is genuinely actionable.
Return JSON only. No preamble. No markdown.
```

---

## Delivery Format

### Daily Brief Structure
1. Top 3 Pain Pulse signals (score >= 7)
2. Top 3 Competitor Move signals (score >= 7)
3. Top 3 Opportunity signals (score >= 7)
4. Upcoming trade shows within 30 days

### Delivery Channels
- React Dashboard (always available)
- Telegram Bot (6AM IST daily)
- WhatsApp Message (6AM IST daily)
- Email via Resend (6AM IST daily)

---

## Environment Variables Required

```
ANTHROPIC_API_KEY=
DATABASE_URL=
REDIS_URL=
RESEND_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
WHATSAPP_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
INSTAGRAM_USERNAME=
INSTAGRAM_PASSWORD=
```

---

## Build Phases

- Phase 1 — Database models + Alembic migrations + Base collector class + Config
- Phase 2 — Collectors (Reddit, RSS, Google Trends, Play Store, News, Instagram)
- Phase 3 — AI Processing (Claude processor, scorer, deduplicator, brief builder)
- Phase 4 — Delivery (Telegram, Email, WhatsApp)
- Phase 5 — Dashboard (FastAPI routes + React frontend)

---

## Business Context

- Bisdom is a two-sided marketplace — Buyers (D2C brands, corporates) and
  Suppliers (textile manufacturers in Tiruppur, Surat, Ludhiana, Ahmedabad,
  Coimbatore)
- The core pain Bisdom solves is "WhatsApp chaos" — fragmented B2B communication
- Primary competitor frustration: IndiaMART charges ₹1.1L–₹2.7L/year for leads
  that don't convert
- This intelligence platform is for internal use — to understand market movements,
  validate product decisions, and identify warm leads
- Geography: Pan-India focus
- Language signals: English, Tamil, Hindi, Gujarati
