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

1. Use search_api to search and scrape the UCCS phonedir website
2. The search_api tool will automatically extract their information and insert them into the database
3. Return the result from search_api
4. If the person is not found, search_api will return: {"found": false}

Important: Do not call insert_person directly - search_api handles extraction and insertion automatically. Only use search_api.
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
    """Search UCCS phone directory using Playwright"""
    try:
        from playwright.async_api import async_playwright
        from bs4 import BeautifulSoup
        import json
        
        async with async_playwright() as p:
            phonedir_url = f"https://phonedir.uccs.edu/employees?search={quote(query)}"
            logger.info("Scraping phonedir: %s", phonedir_url)
            
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(phonedir_url, timeout=15000)
                await page.wait_for_load_state('networkidle')
                
                html = await page.content()
                logger.info("Page HTML (first 1000 chars): %s", html[:1000])
                soup = BeautifulSoup(html, "html.parser")
                app = soup.find("div", id="app")
                logger.info("Found app div: %s", app is not None)
                
                if not app:
                    return '{"found": false}'
                
                data = json.loads(app["data-page"])
                employees = data.get("props", {}).get("employees", {}).get("data", [])
                
                if not employees:
                    logger.info("No employees found for: %s", query)
                    return '{"found": false}'
                
                # Process first result
                employee = employees[0]
                name_parts = employee["name"].split(",")
                first_name = name_parts[1].strip()
                last_name = name_parts[0].strip()
                name = f"{first_name} {last_name}"
                
                department = employee.get("department", {}).get("dept_name", "")
                building = employee.get("building", "")
                room = employee.get("room", "")
                
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
                
            finally:
                await browser.close()
    
    except Exception as e:
        logger.error("Search failed: %s", type(e).__name__, exc_info=True)
        return f"Error: {str(e)}"