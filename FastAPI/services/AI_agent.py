from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import Thinking, WebSearch
import state
import os
from models.OCR_Model import  AddPersonModel

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-test-dummy-key")

instructions = """
You are a university directory lookup assistant. When given a person's name:

1. Search the web for their official university profile using web search
2. Look for:
   - Full name (required)
   - Department (required)
   - School/College (required and given)
   - Building/Office location (optional)
   - Room number (optional)
3. Only extract information from OFFICIAL university sources (staff directory, department pages)
4. Call insert_person with the extracted information
5. Return the complete person record

If you cannot find the person on the web after searching, say "Not found".
Always attempt the web search before giving up.
"""

agent = Agent(
    "gemini-2.0-flash",
    instructions=instructions,
    capabilities=[
        Thinking(),
        WebSearch(local="duckduckgo")
    ]
)



@agent.tool
async def insert_person(
    ctx: RunContext,
    person: AddPersonModel
) -> dict:
    try:
        
        state.db.upsertPerson(person)
        return {
                "status": "success",
                "person": person.model_dump()
            }    
    except Exception as e:
        return {"error": f"Error occurred while inserting person: {e}"}