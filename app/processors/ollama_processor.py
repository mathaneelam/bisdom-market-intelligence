import json
import logging
from typing import Optional
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a market intelligence analyst for Bisdom —
an AI-powered B2B commerce platform for India's textile, garment, manufacturing, and trading SME market.

Your job is to analyse raw signals collected from the internet (Reddit, Quora, LinkedIn, Instagram, Google News, Play Store reviews, textile and garment related news across all news channels, blogs, etc.)
and extract intelligence specifically relevant to Bisdom's business goals.

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
   - General Platform Dissatisfaction (Score 8): ANY negative review or complaint about IndiaMART, TradeIndia, Alibaba, or similar B2B platforms. Even general dissatisfaction like "not satisfied", "bad experience", "not worth it" qualifies. These are gold.
   - The Directory Trap: "indiamart only gives numbers not deals", "alibaba too much spam", "tradeindia leads don't convert", "wasting money on directories"
   - Fake Leads & Sourcing Inefficiencies: "fake buyers", "spam inquiry", "no response", "difficulty finding buyers", "current sourcing process inefficiencies" (Do NOT flag logistics/shipping issues)
   - High Cost Zero ROI: "paid 2 lakh no order", "subscription not worth it", "indiamart renewal waste", "tradeindia waste money"
   - Execution & Negotiation Friction: "too much time evaluating suppliers", "managing negotiations on whatsapp", "comparing prices in spreadsheets", "manual follow-ups taking too long", "lost track of supplier quote"
   - WhatsApp Chaos: "manage on whatsapp difficult", "lost buyer late reply", "no order history whatsapp", "conversation lost vendor"
   - Supplier Verification: "supplier sent wrong quality", "fake manufacturer india", "took advance disappeared", "gsm not matching"
   - Sampling Loop: "3rd sample still wrong", "manufacturer not understanding", "fabric wrong after approval", "sampling round failed"

2. OPPORTUNITY SIGNAL (Score 8-10): Active intent or searching for solutions. Look specifically for:
   - Tier 1 (Immediate): "looking for knitwear/garment manufacturer india", "need fabric supplier india", "have capacity looking for export buyers", "indiamart alternative", "recently funded fashion brand sourcing", "instagram post looking for manufacturer for their fashion brand"
   - Tier 2 (Warm): "failed sampling round", "changing manufacturer", "indiamart subscription expired", "supplier not delivering quality"
   - Tier 3 (Monitor): "new clothing brand launched", "manufacturer capacity available", "comparing b2b platforms india"

3. COMPETITOR MOVE / BIG BRAND STRATEGY (Score 8-10): Focus strictly on EXTERNAL EXECUTION and supply chain strategy from competitors or major fashion brands (like Authentic Brands Group, Locofast, IndiaMART).
   - High Score (Signal): New sourcing strategies, factory partnerships, supply chain expansions, bulk purchasing of raw materials, new B2B features.
   - Low Score (Noise - Score 1-3): Internal corporate news, leadership reshuffles, CEO changes, IPO announcements, stock market updates, or financial earnings reports. Do NOT flag internal corporate drama as important.

4. TRADE SHOW (Score 8-10): Announcements of upcoming B2B textile, apparel, or garment trade shows/exhibitions in India.
5. BRAND LAUNCH (Score 8-10): News about a new D2C clothing, apparel, or fashion brand launching in India.

For each signal, return ONLY valid JSON with:
- summary: one line, what this signal says
- relevance_score: 1-10 (10 = directly actionable for Bisdom, 1-3 = generic industry news)
- sentiment: positive | negative | neutral
- tags: array of relevant tags
- insight: one line explaining why this matters for Bisdom
- stream: pain_pulse | competitor_move | opportunity_signal | trade_show | brand_launch | other
- trade_show_details: (ONLY if stream is 'trade_show') A JSON object containing: "name" (str), "city" (str), "venue" (str), "start_date" (str, YYYY-MM-DD format if known), "end_date" (str, YYYY-MM-DD if known)

Only score above 7 if the signal strictly matches the definitions above and is directly relevant to the Indian B2B market.
Return JSON only. No preamble. No markdown."""

DEDUP_SYSTEM = """You are an assistant that finds semantically duplicate market intelligence signals.
Given a list of signals with their IDs and summaries, identify which signals are saying the exact same thing (semantic duplicates).
For any group of duplicates, pick one as the 'primary' and list the others as 'duplicates'.

Return ONLY valid JSON in this exact format:
{
  "duplicate_ids": ["uuid-of-duplicate-1", "uuid-of-duplicate-2"]
}

If there are no duplicates, return {"duplicate_ids": []}.
Return JSON only. No preamble. No markdown."""

MATCH_SYSTEM = """You are a pattern clustering assistant for Bisdom market intelligence.

Given a NEW signal and a list of EXISTING patterns, determine if the signal belongs to an existing pattern or is a new one.

Rules:
- Match if the signal describes the SAME core problem/opportunity, even with different wording
- "spam calls from IndiaMART" and "barrage of phone calls after posting" are the SAME pattern
- "fake leads" and "wrong quality supplier" are DIFFERENT patterns
- Be strict: only match if the core issue is truly the same

Return ONLY valid JSON:
{
  "match": true/false,
  "pattern_id": "uuid-of-matched-pattern" or null,
  "new_pattern": null or {
    "name": "Short pattern name (under 80 chars)",
    "description": "One paragraph explaining the recurring issue",
    "bisdom_action": "What Bisdom should do about this pattern"
  }
}

JSON only. No preamble. No markdown."""


class OllamaProcessor:
    """Scores raw signals using Ollama (OpenAI-compatible API)."""

    def __init__(self):
        api_key = settings.OLLAMA_API_KEY or "ollama"
        base_url = settings.OLLAMA_BASE_URL or "http://localhost:11434/v1"
        self.model = settings.OLLAMA_MODEL or "llama3"
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        self.fallback_client: Optional[AsyncOpenAI] = None
        if settings.OLLAMA_API_KEY_FALLBACK:
            self.fallback_client = AsyncOpenAI(api_key=settings.OLLAMA_API_KEY_FALLBACK, base_url=base_url)

    async def _create_completion(self, **kwargs):
        try:
            return await self.client.chat.completions.create(**kwargs)
        except Exception as e:
            if not self.fallback_client:
                raise
            logger.warning("Primary Ollama key failed (%s), retrying with fallback key", e)
            return await self.fallback_client.chat.completions.create(**kwargs)

    async def analyze_signal(self, raw_content: str, default_stream: str = "unknown") -> Optional[dict]:
        try:
            response = await self._create_completion(
                model=self.model,
                max_tokens=512,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": raw_content},
                ],
            )

            text = response.choices[0].message.content.strip()

            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            data = json.loads(text.strip())

            for key in ["summary", "relevance_score", "sentiment", "tags", "insight", "stream"]:
                if key not in data:
                    data[key] = default_stream if key == "stream" else None

            return data

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from Ollama: %s", e)
            return None
        except Exception as e:
            logger.error("Error calling Ollama: %s", e)
            return None

    async def find_duplicates(self, payload: str) -> list[str]:
        try:
            response = await self._create_completion(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": DEDUP_SYSTEM},
                    {"role": "user", "content": payload},
                ],
            )

            text = response.choices[0].message.content.strip()

            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            data = json.loads(text.strip())
            return data.get("duplicate_ids", [])

        except Exception as e:
            logger.error("Error calling Ollama for dedup: %s", e)
            return []

    async def match_pattern(self, prompt: str) -> Optional[dict]:
        try:
            response = await self._create_completion(
                model=self.model,
                max_tokens=512,
                messages=[
                    {"role": "system", "content": MATCH_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            )

            text = response.choices[0].message.content.strip()

            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            return json.loads(text.strip())

        except Exception as e:
            logger.error("Pattern matching error via Ollama: %s", e)
            return None
