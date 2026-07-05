# Bisdom Market Intelligence Platform — Master Context

## What This Project Is

A standalone market intelligence platform for Bisdom — an AI-powered B2B commerce
platform targeting India's SME market in textile, garment, manufacturing, raw
materials, retail and wholesale sectors.

This platform continuously collects signals from the internet, processes them with
the Ollama/AI scoring engine, and delivers a daily morning intelligence brief via Dashboard, Telegram,
WhatsApp and Email — at zero subscription cost.

---

## Tech Stack

| Layer            | Technology                              |
| ---------------- | --------------------------------------- |
| Backend          | FastAPI                                 |
| Database         | PostgreSQL (Neon free tier)             |
| Scheduler        | APScheduler (inside FastAPI)            |
| Job Queue        | Redis + ARQ (Upstash free tier)         |
| AI Processing    | AI Processor (Ollama/LLM)               |
| Email Delivery   | Resend.com (free tier)                  |
| Telegram         | Telegram Bot API (free)                 |
| WhatsApp         | WhatsApp Business Cloud API (free tier) |
| Dashboard        | React + Vanilla CSS (Aesthetic Dark)    |
| Hosting          | Railway (Production API deployment)     |
| Frontend Hosting | Vercel (Production Client deployment)   |

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
│   │   ├── rss_feeds.py
│   │   ├── instagram.py
│   │   ├── linkedin.py
│   │   ├── google_trends.py
│   │   ├── play_store.py
│   │   └── news.py
│   │
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── ollama_processor.py
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
│       ├── competitor.py
│       └── trade_show.py
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Signals.jsx
│       │   ├── Sources.jsx
│       │   ├── Competitors.jsx
│       │   └── TradeShows.jsx
│       └── components/
│           └── Layout.jsx
│
├── migrations/
├── scripts/
│   ├── clean_international_signals.py
│   └── diagnose_dns.py
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
```

---

## Intelligence Streams & Keywords (India-Only Focus)

All intelligence streams are strictly targeted at **India's domestic market**, focusing on key textile hubs like Tiruppur, Surat, Ludhiana, Ahmedabad, and Coimbatore.

### Stream 1 — Pain Pulse
* **Description:** Sourcing complaints, lead failures, and directory issues on existing Indian platforms.
* **Keywords (Reddit & Search):**
  - `"IndiaMART fake leads"`
  - `"B2B platform complaint India"`
  - `"garment sourcing problem India"`
  - `"manufacturer WhatsApp chaos India"`
  - `"textile supplier fraud India"`
  - `"IndiaMART renewal not worth it"`
  - `"sourcing vendor problem India"`

### Stream 2 — Competitor Move
* **Description:** Strategy updates and platform expansions from direct B2B market competitors.
* **Keywords (Google News):**
  - `"IndiaMART new feature"`
  - `"Fiber2Fashion launch"`
  - `"Locofast update"`
  - `"Fashinza funding"`
  - `"B2B textile platform India launch"`

### Stream 3 — Opportunity Signal (Garment Buyers Only)
* **Description:** Direct sourcing requests, collection launches, and factory needs from clothing brands, boutiques, and startup fashion labels.
* **Instagram Hashtags:**
  - `#clothingbrand`
  - `#fashionbrand`
  - `#clothingbrandindia`
  - `#fashionbrandindia`
  - `#clothinglabelindia`
  - `#d2cbrandindia`
  - `#boutiqueindia`
  - `#clothingstartup`
* **LinkedIn Search Queries (via Google Index):**
  - `site:linkedin.com/posts ("looking for garment manufacturer" OR "looking for fabric supplier" OR "need garment manufacturer") AND ("India" OR "Indian" OR "Tiruppur" OR "Surat" OR "Ludhiana" OR "Mumbai" OR "Delhi" OR "Ahmedabad" OR "Coimbatore")`
  - `site:linkedin.com/posts ("sourcing clothing brand" OR "clothing brand manufacturer" OR "looking for knitwear manufacturer") AND ("India" OR "Indian" OR "Tiruppur" OR "Surat" OR "Ludhiana" OR "Ahmedabad" OR "Coimbatore")`

---

## Collector Schedule

| Job                 | Cadence                     |
| ------------------- | --------------------------- |
| Google News RSS     | Every 6 hours               |
| LinkedIn RSS Search | Every 8 hours               |
| Instagram hashtags  | Every 12 hours              |
| Play Store reviews  | Every 12 hours              |
| Reddit Collector    | Every 12 hours              |
| Google Trends       | Daily 2:00 AM IST           |
| AI Scorer           | Daily 5:00 AM IST           |
| Brief builder       | Daily 5:30 AM IST           |
| Delivery (all 3)    | Daily 6:00 AM IST           |

---

## AI Processing — System Prompt

The scoring processor evaluates signals using the following instructions:

```text
You are a market intelligence analyst for Bisdom —
an AI-powered B2B commerce platform for India's textile, garment, manufacturing, and trading SME market.

Your job is to analyse raw signals collected from the internet (Reddit, Quora, LinkedIn, Instagram, Google News, Play Store reviews, textile and garment related news across all news channels, blogs, etc.) and extract intelligence specifically relevant to Bisdom's business goals.

### WHAT TO IGNORE (STRICT NOISE FILTER - Score 1-3)
You will encounter a lot of generic retail and fashion news. You MUST score the following types of articles as a 1, 2, or 3. They are NOISE and do not generate B2B leads for Bisdom:
- Corporate Earnings & Financials: (e.g., "Abercrombie reports Q1 sales", "Brand X stock rises")
- Mergers & Acquisitions: (e.g., "JD.com interested in buying The Very Group")
- Generic Industry Analyst Reports: (e.g., "How returns friction is slowing sales", "GlobalData market analysis")
- High-Level Sustainability/ESG Panels: (e.g., "Decarbonisation risks leaving workers behind")
- Internal Corporate Drama: (e.g., "Authentic Brands reshuffles leadership", CEO appointments, IPOs)
- Non-India Content (STRICT NOISE FILTER): Any news, posts, or sourcing requests that are not related to or originating from India. Bisdom is strictly focused on the Indian B2B market (e.g. textile hubs like Tiruppur, Surat, Ludhiana, Ahmedabad, Coimbatore). Any posts or news about foreign brands, international factories (e.g. in Bangladesh, Vietnam, China, US, UK), or non-India sourcing requests MUST be scored as a 1, 2, or 3.

### DEFINITION OF HIGH-VALUE SIGNALS

1. PAIN PULSE (Score 8-10): Complaints about existing platforms or processes. Look specifically for:
   - General Platform Dissatisfaction (Score 8)
   - The Directory Trap
   - Fake Leads & Sourcing Inefficiencies
   - High Cost Zero ROI
   - Execution & Negotiation Friction
   - WhatsApp Chaos
   - Supplier Verification
   - Sampling Loop

2. OPPORTUNITY SIGNAL (Score 8-10): Active intent or searching for solutions. Look specifically for:
   - Tier 1 (Immediate)
   - Tier 2 (Warm)
   - Tier 3 (Monitor)

3. COMPETITOR MOVE / BIG BRAND STRATEGY (Score 8-10): Focus strictly on EXTERNAL EXECUTION and supply chain strategy from competitors or major fashion brands (like Authentic Brands Group, Locofast, IndiaMART).

4. TRADE SHOW (Score 8-10): Announcements of upcoming B2B textile, apparel, or garment trade shows/exhibitions in India.

5. BRAND LAUNCH (Score 8-10): News about a new D2C clothing, apparel, or fashion brand launching in India.

For each signal, return ONLY valid JSON with:
- summary: one line, what this signal says
- relevance_score: 1-10 (10 = directly actionable for Bisdom, 1-3 = generic industry news)
- sentiment: positive | negative | neutral
- tags: array of relevant tags
- insight: one line explaining why this matters for Bisdom
- stream: pain_pulse | competitor_move | opportunity_signal | trade_show | brand_launch | other
- trade_show_details: (ONLY if stream is 'trade_show')

Only score above 7 if the signal strictly matches the definitions above and is directly relevant to the Indian B2B market.
Return JSON only. No preamble. No markdown.
```

---

## Build Phases

*   **[x] Phase 1: Database & Migrations** — Completed. Models initialized, PostgreSQL migrations applied via Alembic, Base collector framework set up.
*   **[x] Phase 2: Collectors** — Completed. Automated scrapers written for Reddit, RSS feeds, Google Trends, Play Store reviews, Google News, Instagram hashtags, and LinkedIn RSS search.
*   **[x] Phase 3: AI Processing** — Completed. Ollama/AI integration created with prompts for scoring, tagging, summarization, and duplication checks.
*   **[x] Phase 4: Delivery Channels** — Completed. Configured daily Morning Brief generators delivering to Email (Resend), Telegram (Bot API), and WhatsApp.
*   **[x] Phase 5: Dashboard Frontend** — Completed. dark-mode dashboard built with routing, real-time filters, "Sources" card grids, and clickable snippet links to original posts.
