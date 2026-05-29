import json
import logging
import google.generativeai as genai
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a market intelligence analyst for Bisdom —
an AI-powered B2B commerce platform for India's textile, garment, and manufacturing SME market.

Your job is to analyse raw signals collected from the internet (Reddit, Play Store reviews, etc.)
and extract intelligence specifically relevant to Bisdom's business goals.

### DEFINITION OF HIGH-VALUE SIGNALS

1. PAIN PULSE (Score 8-10): Complaints about existing platforms or processes. Look specifically for:
   - Fake / Junk Leads: "fake buyers", "spam inquiry", "no response after inquiry", "time waste leads", "junk leads"
   - High Cost Zero ROI: "indiamart renewal waste", "paid 2 lakh no order", "subscription not worth it", "tradeindia waste money"
   - WhatsApp Chaos: "manage on whatsapp difficult", "lost buyer late reply", "no order history whatsapp", "conversation lost vendor"
   - Supplier Verification: "supplier sent wrong quality", "fake manufacturer india", "took advance disappeared", "gsm not matching"
   - Sampling Loop: "3rd sample still wrong", "manufacturer not understanding", "fabric wrong after approval", "sampling round failed"

2. OPPORTUNITY SIGNAL (Score 8-10): Active intent or searching for solutions. Look specifically for:
   - Tier 1 (Immediate): "looking for knitwear/garment manufacturer india", "need fabric supplier india", "have capacity looking for export buyers", "indiamart alternative", "recently funded fashion brand sourcing"
   - Tier 2 (Warm): "failed sampling round", "changing manufacturer", "indiamart subscription expired", "supplier not delivering quality"
   - Tier 3 (Monitor): "new clothing brand launched", "manufacturer capacity available", "comparing b2b platforms india"

3. COMPETITOR MOVE: Any significant update, feature, or pricing change from IndiaMART, TradeIndia, Alibaba, Fiber2Fashion, Locofast, or Fashinza.

For each signal, return ONLY valid JSON with:
- summary: one line, what this signal says
- relevance_score: 1-10 (10 = directly actionable for Bisdom, 1-3 = generic industry news)
- sentiment: positive | negative | neutral
- tags: array of relevant tags
- insight: one line explaining why this matters for Bisdom
- stream: pain_pulse | competitor_move | opportunity_signal | other

Only score above 7 if the signal strictly matches the definitions above.
Return JSON only. No preamble. No markdown."""

class GeminiProcessor:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=SYSTEM_PROMPT)
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY is not set. Processor will return mocked data.")

    async def analyze_signal(self, raw_content: str, default_stream: str = "unknown") -> Optional[dict]:
        """
        Sends the raw content to Gemini and parses the returned JSON.
        """
        if not self.model:
            # Fallback for testing without API key
            return {
                "summary": f"Mock summary of: {raw_content[:50]}...",
                "relevance_score": 5,
                "sentiment": "neutral",
                "tags": ["mock"],
                "insight": "Mock insight",
                "stream": default_stream
            }

        try:
            # We use generation_config to ask for JSON output if supported, 
            # or just rely on the prompt instructions.
            response = await self.model.generate_content_async(
                raw_content,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                )
            )
            
            result_text = response.text.strip()
            # Strip markdown code blocks if the model still outputs them despite prompt
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
                
            data = json.loads(result_text.strip())
            
            # Ensure required fields exist
            expected_keys = ["summary", "relevance_score", "sentiment", "tags", "insight", "stream"]
            for key in expected_keys:
                if key not in data:
                    data[key] = default_stream if key == "stream" else None
                    
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini: {e}\nRaw output: {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return None
