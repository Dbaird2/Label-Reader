from pydantic_ai import Agent, RunContext
import state
from models.OCR_Model import  AddPersonModel
import logging

logger = logging.getLogger(__name__)

instructions = """
You are a UCCS directory lookup assistant. When given a person's name:

1. Find their department and building location in the UCCS directory
2. Call insert_person with: name, department, building, and room (if available)
3. Return the complete person record

Only use official UCCS directory information. If you cannot find the person, say "Not found".
Do NOT guess or make up information.
"""

agent = Agent(
    "gemini-2.0-flash",
    instructions=instructions
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
        logger.error("Error inserting person: %s", e)
        return {"status": "error", "error": str(e)}