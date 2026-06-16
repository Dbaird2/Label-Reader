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

1. Use search_api to find the person in the UCCS phonedir API
2. The search_api tool will automatically extract their information and insert them into the database
3. Return the result from search_api
4. If the person is not found, search_api will return: {"found": false}

Important: Do not call insert_person directly - search_api handles insertion automatically. Only use search_api.
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
async def search_api(
    ctx: RunContext,
    query: str
) -> str:
    """Search UCCS phone directory API for person info"""
    try:
        async with aiohttp.ClientSession() as session:
            api_url = f"https://phonedir.uccs.edu/api/employees?search={quote(query)}"
            
            logger.info("Searching API: %s", api_url)
            async with session.get(api_url, timeout=10) as resp:
                if resp.status != 200:
                    logger.error("API returned status %s", resp.status)
                    return f"API search failed (status {resp.status})"
                
                data = await resp.json()
                people = data.get("data", [])
                
                if not people:
                    logger.info("No results found for: %s", query)
                    return '{"found": false}'
                
                # Process first result
                person = people[0]
                name_parts = person["name"].split(",")
                first_name = name_parts[1].strip()
                last_name = name_parts[0].strip()
                name = f"{first_name} {last_name}"
                
                department = person.get("department", {}).get("dept_name", "")
                building = person.get("building", "")
                room = person.get("room", "")
                
                logger.info("Found: %s, Dept: %s, Building: %s, Room: %s", name, department, building, room)
                
                # Insert into database
                result = await insert_person(ctx, AddPersonModel(
                    name=name,
                    department=department,
                    building=building,
                    room=room,
                    school="UCCS"
                ))
                
                return str(result)
                
    except Exception as e:
        logger.error("Search failed: %s", type(e).__name__, exc_info=True)
        return f"Error: {str(e)}"