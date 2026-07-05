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
│   │   ├── pattern_matcher.py
│   │   ├── content_generator.py
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
│   │   ├── trade_shows.py
│   │   ├── patterns.py
│   │   └── content.py
│   │
│   └── models/
│       ├── __init__.py
│       ├── signal.py
│       ├── processed_signal.py
│       ├── brief.py
│       ├── competitor.py
│       ├── trade_show.py
│       ├── pattern.py
│       ├── signal_pattern.py
│       └── content_piece.py
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Signals.jsx
│       │   ├── Sources.jsx
│       │   ├── Competitors.jsx
│       │   ├── TradeShows.jsx
│       │   └── ContentBank.jsx
│       └── components/
│           ├── Layout.jsx
│           ├── PlatformPreview.jsx
│           └── contentBankShared.jsx
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

-- Recurring pain/opportunity themes, clustered from processed_signals by the LLM
CREATE TABLE patterns (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              VARCHAR(200),
    description       TEXT,
    category          VARCHAR(50),   -- pain_pulse, opportunity_signal, competitor_move
    bisdom_action     TEXT,
    signal_count      INTEGER DEFAULT 1,
    trend             VARCHAR(20) DEFAULT 'new',   -- new, growing, stable, declining
    importance_score  INTEGER DEFAULT 50,
    first_seen        DATE DEFAULT CURRENT_DATE,
    last_seen         DATE DEFAULT CURRENT_DATE,
    created_at        TIMESTAMP DEFAULT NOW()
);

-- Content Bank: one pattern -> one calendar day -> one row per platform format.
-- image_brief/comment_note/scheduled_date added 2026-07-05 for the weekly calendar redesign.
CREATE TABLE content_pieces (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id         UUID REFERENCES patterns(id),
    audience           VARCHAR(20),   -- buyer | supplier
    format             VARCHAR(20),   -- linkedin | linkedin_article | instagram_post | instagram_reel | whatsapp | email | blog
    tone               VARCHAR(20),   -- educational | contrast
    title              TEXT,
    body               TEXT,
    image_brief        TEXT,          -- AI-written description of the accompanying visual (no image model wired up)
    comment_note       TEXT,          -- author's first-comment text
    scheduled_date     DATE,          -- the calendar day this piece belongs to
    source_review_ids  UUID[],        -- receipts: the real signals this content is grounded in
    model              VARCHAR(50),
    status             VARCHAR(20) DEFAULT 'draft',  -- draft | approved | posted | rejected
    created_at         TIMESTAMP DEFAULT NOW()
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

### Stream 3 — Opportunity Signal
* **Description:** Direct sourcing requests, collection launches, and factory needs. Audience focus is deliberately different per source (set 2026-07-05): Instagram stays buyer-only by design; LinkedIn and Reddit cover both buyers (brands looking for manufacturers) and suppliers (manufacturers with capacity looking for buyers).
* **Instagram Hashtags (buyer-only):**
  - `#clothingbrand`
  - `#fashionbrand`
  - `#clothingbrandindia`
  - `#fashionbrandindia`
  - `#clothinglabelindia`
  - `#d2cbrandindia`
  - `#boutiqueindia`
  - `#clothingstartup`
* **LinkedIn Search Queries (via Google Index):**
  - `site:linkedin.com/posts ("looking for garment manufacturer" OR "looking for fabric supplier" OR "need garment manufacturer") AND ("India" OR "Indian" OR "Tiruppur" OR "Surat" OR "Ludhiana" OR "Mumbai" OR "Delhi" OR "Ahmedabad" OR "Coimbatore")` (buyer)
  - `site:linkedin.com/posts ("sourcing clothing brand" OR "clothing brand manufacturer" OR "looking for knitwear manufacturer") AND ("India" OR "Indian" OR "Tiruppur" OR "Surat" OR "Ludhiana" OR "Ahmedabad" OR "Coimbatore")` (buyer)
  - `site:linkedin.com/posts ("garment manufacturer" OR "textile factory" OR "knitwear manufacturer") AND ("export ready" OR "looking for buyers" OR "spare capacity" OR "MOQ available") AND ("India" OR "Tiruppur" OR "Surat" OR "Ludhiana" OR "Coimbatore")` (supplier, added 2026-07-05)
* **Reddit Keywords:**
  - Buyer: `"looking for garment manufacturer India"`, `"fabric supplier India MOQ"`, `"clothing brand manufacturer India"`, `"D2C brand sourcing India"`, `"knitwear manufacturer India"`, `"need textile supplier India"`, `"recommend fabric manufacturer India"`
  - Supplier (added 2026-07-05): `"manufacturer looking for buyers India"`, `"garment factory export capacity India"`, `"textile mill surplus capacity India"`

---

## Collector Schedule

| Job                 | Cadence                     |
| ------------------- | --------------------------- |
| RSS feeds           | Every 6 hours               |
| Reddit Collector    | Every 4 hours               |
| Play Store reviews  | Every 12 hours              |
| Google Trends       | Every 12 hours              |
| Google News RSS     | Every 12 hours (was 8h, dropped 2026-07-05 — `when:7d` on the query keeps it fresh without a 3rd daily fetch) |
| Instagram hashtags  | Every 12 hours              |
| LinkedIn RSS Search | Every 12 hours (was 8h, same reasoning as Google News) |
| AI Scorer           | Daily 5:00 AM IST — processes pain_pulse + newest signals first (added 2026-07-05, was unordered) |
| Pattern Matcher     | Daily 5:15 AM IST           |
| Brief builder       | Daily 5:30 AM IST           |
| Content Generator   | Daily 5:45 AM IST — tops up a rolling 7-day content calendar; no-ops once the week is full (see Content Bank below) |
| Delivery (Telegram) | Daily 6:00 AM IST           |
| Bin cleanup         | Daily 3:00 AM IST — purges recycle-bin records older than 7 days |

**Recency cutoffs (added 2026-07-05, to stop stale signals from reaching the AI scorer):** Google News & LinkedIn RSS queries append `when:7d`; Play Store reviews older than 60 days are skipped; Instagram posts older than 7 days are skipped; Reddit is already `sort=new` on both its OAuth and RSS paths.

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
*   **[x] Phase 6: Pattern Matching & Content Bank** — Completed 2026-07-05. `pattern_matcher.py` clusters processed signals into recurring pain/opportunity themes (`patterns` table). `content_generator.py` turns high-importance patterns into ready-to-review marketing content (`content_pieces` table): one pattern per calendar day, batched a rolling 7 days ahead, audience rotated ~70% buyer / 30% supplier, and repurposed across LinkedIn (post + article), Instagram (post + reel), WhatsApp, Email, and Blog. Each piece includes an AI-written image brief and a first-comment note. The "Content Bank" dashboard page renders a weekly calendar of platform-native mockups with Approve/Decline/Edit/Posted actions, alongside a flat filterable list view.
