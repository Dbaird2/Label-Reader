import asyncio

from pydantic_ai import Agent, RunContext
import state
from models.OCR_Model import  AddPersonModel, SearchPersonModel
import logging
import os
import aiohttp
from urllib.parse import quote

logger = logging.getLogger(__name__)

system_prompt = """You are correcting OCR text from shipping labels.

CRITICAL RULES:
- Do NOT add letters that aren't in the input. If the input is "chrlssle", you CANNOT add an 'a'.
- Only substitute/remove/reorder characters that are already present.
- Character count should stay roughly the same (±1-2 letters max for noise).

Common OCR confusions to fix:
- l (lowercase L) ↔ i, I (uppercase I) — "Jl" could be "Ji"
- 0 (zero) ↔ O (uppercase O) — "K0ren" → "Karen"
- 1 (one) ↔ l (lowercase L), I (uppercase I) — "1ohn" → "John"
- rn ↔ m — "Tarn" could be "Tam" or vice versa
- u ↔ o — "Dcug" could be "Doug"

Examples of what to do:
- "Chrissie" with OCR errors "chrlssle" → "chrissie" (fix l→i)
- "Jennifer" as "Jenni|er" → "Jennifer"
- "Michael" as "M1chae1" → "Michael"

Examples of what NOT to do:
- "chrlssle" → "charlse" ❌ (added 'a', changed structure)
- "ab" → "alice" ❌ (added letters not in input)
- "xyz" → "xyz" ✓ (kept as-is if unintelligible)

Return ONLY the corrected name, nothing else.
If completely unintelligible, return the original text."""

agent = Agent(
    "gpt-4o-mini", 
    system_prompt=system_prompt
)

async def run_agent_with_timeout(search_model: SearchPersonModel | str, timeout: int = 5) -> str:
    try:
        result = await agent.run(search_model.search if isinstance(search_model, SearchPersonModel) else search_model)
        logger.info("AI agent corrected '%s' to '%s'", search_model.search if isinstance(search_model, SearchPersonModel) else search_model, result)
        corrected_name= result.data
        logger.info("AI agent corrected '%s' to '%s'", search_model.search if isinstance(search_model, SearchPersonModel) else search_model, corrected_name)
        if corrected_name and corrected_name != search_model.search:
            ai_match = await state.db.lookupName(corrected_name)
            if ai_match and ai_match["confidence"] > 0.4:
                logger.info("AI-corrected name '%s' has a good DB match, returning AI-corrected result", corrected_name)
                return ai_match
            else:
                logger.info("AI-corrected name '%s' does not have a good DB match, returning original candidate", corrected_name)
                return {"error": f"No valid match found for '{search_model.search}' after AI correction"}
        else:
            logger.info("AI agent did not provide a correction, returning original candidate")
            return {"error": f"No valid match found for '{search_model.search}' after AI correction"}
    except asyncio.TimeoutError:
        logger.warning("AI agent timed out after %d seconds for input '%s'", timeout, corrected_name)
        return {"error": f"AI agent timed out after {timeout} seconds"}