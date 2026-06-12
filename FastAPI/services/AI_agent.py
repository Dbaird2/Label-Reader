from pydantic_ai import Agent, RunContext
import state
from models.OCR_Model import  AddPersonModel
import logging
import os
import aiohttp


logger = logging.getLogger(__name__)

instructions = """
You are a UCCS directory lookup assistant. When given a person's name:

1. Use search_web to find the person on UCCS site (search for: "{name} site:uccs.edu")
2. Extract: department, building, room, school='UCCS'
3. Call insert_person with the extracted data if department is found
4. If not found after searching, say "Null"
5. Do NOT guess - only use information from actual search results
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
        return {
            "status": "success",
            "person": person.model_dump()
        }    
    except Exception as e:
        logger.error("Error inserting person: %s", e)
        return {"status": "error", "error": str(e)}
    
@agent.tool
async def search_web(
    ctx: RunContext,
    query: str
) -> str:
    """Search the web for information"""
    try:
        async with aiohttp.ClientSession() as session:
            # Using DuckDuckGo (free, no API key needed) or Google Search
            search_url = f"https://duckduckgo.com/?q={query}&format=json"
            
            async with session.get(search_url, timeout=5) as resp:
                if resp.status == 200:
                    results = await resp.json()
                    # Format results for the agent
                    snippets = []
                    for result in results.get('Results', [])[:3]:
                        snippets.append(f"{result.get('Title')}: {result.get('FirstURL')}")
                    return "\n".join(snippets) if snippets else "No results found"
        
        return "Search failed"
    except Exception as e:
        logger.error("Web search failed: %s", e)
        return f"Error: {str(e)}"