from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import Thinking, WebSearch
import state
import os
from models.OCR_Model import  AddPersonModel

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-test-dummy-key")

instructions = """
You help maintain a university staff directory.

When asked to add a person:

1. Search the web for the person's official university profile.
2. Extract:
   - name
   - department
   - school
   - building (if available)
   - room (if available)
3. Only use information from official university sources.
4. If multiple people match or confidence is below 80%, ask for clarification.
5. When sufficient information is available, call insert_person.

If building or room cannot be found from an official source,
set them to null and continue.
"""
agent = Agent(
    "openai:gpt-4.1",
    api_key=OPENAI_API_KEY,  
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