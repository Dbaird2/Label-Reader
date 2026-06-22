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
The input is raw OCR output that may contain:
- Missing or extra letters (i/l confusion, 1/l/I)
- Transpositions (Jon -> Jno)
- Partial words
- Extra noise

Your job: Return your best guess at what the actual person's name is.
Return ONLY the corrected name, nothing else.
If you're uncertain, return your best guess anyway.
Keep it to first name + last name format (e.g. "John Smith").
If the input is empty, return an empty string.
If the input does not look like a name at all (e.g., addresses, numbers only), return it unchanged.
If it's completely unintelligible, return the original text."""

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