import asyncio

from pydantic_ai import Agent, RunContext
import state
from models.OCR_Model import  AddPersonModel
import logging
import os
import aiohttp
from urllib.parse import quote

logger = logging.getLogger(__name__)

system_prompt = """
You are a UCCS directory lookup assistant. When given a person's name:

1. Use search_web to find the person in the UCCS phonedir employees directory
2. Parse the search results HTML to extract: name, department, building (if available), room (if available)
3. Call insert_person with the extracted information: name, department, building, room, school='UCCS'
4. Return the result from insert_person
5. If the person is not found in the search results, return: {"found": false}

Important: Only extract information from actual search results. Do not guess or fabricate data.
"""

agent = Agent(
    "gpt-4o-mini", 
    system_prompt=system_prompt
)

@agent.tool
async def insert_person(
    ctx: RunContext,
    person: AddPersonModel
) -> dict:
    try:
        logger.info("AI Agent inserting person into DB: %s", person)
        await state.db.upsertPerson(person)
        return person.model_dump()  # Just return the person data
    except Exception as e:
        logger.error("Error inserting person: %s", e)
        return {"error": str(e)}
    
@agent.tool
async def search_web(
    ctx: RunContext,
    query: str
) -> str:
    """Search Google for UCCS directory info"""
    try:
        async with aiohttp.ClientSession() as session:
            # Search Google for UCCS directory info
            search_query = f'"{query}" UCCS site:uccs.edu'
            google_url = f"https://www.google.com/search?q={quote(search_query)}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            logger.info("Google search URL: %s", google_url)
            async with session.get(google_url, headers=headers, timeout=10) as resp:
                logger.info("Google response status: %s", resp.status)
                if resp.status == 200:
                    content = await resp.text()
                    logger.info("Google response length: %d", len(content))
                    return content
                else:
                    logger.error("Google returned status %s", resp.status)
                    return f"Search failed (status {resp.status})"
            
    except Exception as e:
        logger.error("Search failed: %s", type(e).__name__, exc_info=True)
        return f"Error: {str(e)}"