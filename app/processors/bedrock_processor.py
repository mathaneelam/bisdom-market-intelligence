"""
AI signal processor using AWS Bedrock — Claude Haiku 4.5.

Replaces the Gemini processor with zero changes to the scorer/deduplicator
interface. Just swap the import.
"""
import json
import logging
import boto3
from typing import Optional

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

### DEFINITION OF HIGH-VALUE SIGNALS

1. PAIN PULSE (Score 8-10): Complaints about existing platforms or processes. Look specifically for:
   - Fake Leads & Sourcing Inefficiencies: "fake buyers", "spam inquiry", "no response", "difficulty finding buyers", "current sourcing process inefficiencies" (Do NOT flag logistics/shipping issues)
   - High Cost Zero ROI: "indiamart renewal waste", "paid 2 lakh no order", "subscription not worth it", "tradeindia waste money"
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

Only score above 7 if the signal strictly matches the definitions above.
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

MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


def _get_client():
    """Create a Bedrock Runtime client."""
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


class BedrockProcessor:
    """Scores raw signals using Claude Haiku 4.5 on AWS Bedrock."""

    def __init__(self):
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self.client = _get_client()
        else:
            self.client = None
            logger.warning("AWS credentials not set. Processor will return mocked data.")

    async def analyze_signal(self, raw_content: str, default_stream: str = "unknown") -> Optional[dict]:
        if not self.client:
            return {
                "summary": f"Mock summary of: {raw_content[:50]}...",
                "relevance_score": 5,
                "sentiment": "neutral",
                "tags": ["mock"],
                "insight": "Mock insight — set AWS credentials to enable real analysis.",
                "stream": default_stream,
            }

        try:
            response = self.client.invoke_model(
                modelId=MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 512,
                    "system": SYSTEM_PROMPT,
                    "messages": [
                        {"role": "user", "content": raw_content}
                    ],
                }),
            )

            result = json.loads(response["body"].read())
            text = result["content"][0]["text"].strip()

            # Strip markdown fences if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            data = json.loads(text.strip())

            # Ensure required fields
            for key in ["summary", "relevance_score", "sentiment", "tags", "insight", "stream"]:
                if key not in data:
                    data[key] = default_stream if key == "stream" else None

            return data

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from Bedrock: %s", e)
            return None
        except Exception as e:
            logger.error("Error calling Bedrock: %s", e)
            return None

    async def find_duplicates(self, payload: str) -> list[str]:
        """Used by the deduplicator to find semantic duplicates."""
        if not self.client:
            return []

        try:
            response = self.client.invoke_model(
                modelId=MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "system": DEDUP_SYSTEM,
                    "messages": [
                        {"role": "user", "content": payload}
                    ],
                }),
            )

            result = json.loads(response["body"].read())
            text = result["content"][0]["text"].strip()

            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            data = json.loads(text.strip())
            return data.get("duplicate_ids", [])

        except Exception as e:
            logger.error("Error calling Bedrock for dedup: %s", e)
            return []
