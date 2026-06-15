from pydantic_ai import Agent, RunContext
import state
from models.OCR_Model import  AddPersonModel
import logging
import os
import aiohttp


logger = logging.getLogger(__name__)

instructions = """
You are a UCCS directory lookup assistant. When given a person's name:

1. Use search_web to find the person's info on UCCS sites
2. Extract: name, department, building (if available), room (if available)
3. Call insert_person with: name, department, building, room, school='UCCS'
4. Return the result from insert_person
5. If you cannot find any information, return: {"found": false}

Only use information found in actual search results. Do not guess.
"""

agent = Agent(
    "gpt-4o-mini", 
    instructions=instructions 
)

@agent.tool
async def insert_person(
    ctx: RunContext,
    person: AddPersonModel
) -> dict:
    try:
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
    """Search the web and return page content"""
    try:
        async with aiohttp.ClientSession() as session:
            search_url = f"https://duckduckgo.com/?q={query}&format=json"
            
            async with session.get(search_url, timeout=5) as resp:
                if resp.status == 200:
                    results = await resp.json()
                    content_chunks = []
                    
                    for result in results.get('Results', [])[:4]:
                        url = result.get('FirstURL')
                        logger.info("Fetching URL: %s", url)
                        try:
                            async with session.get(url, timeout=5) as page_resp:
                                logger.info("Fetched URL %s with status %s", url, page_resp.status)
                                if page_resp.status == 200:
                                    content = await page_resp.text()
                                    logger.info("Content length for URL %s: %d", url, len(content))
                                    content_chunks.append(content[:2000])
                        except Exception as e:
                            logger.error("Error fetching URL %s: %s", url, e)
                            pass
                    
                    return "\n".join(content_chunks) if content_chunks else "No results found"
        
        return "Search failed"
    except Exception as e:
        logger.error("Web search failed: %s", e)
        return f"Error: {str(e)}"