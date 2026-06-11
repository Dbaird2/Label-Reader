from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import Thinking, WebSearch
import state
import os
from models.OCR_Model import  OCRResult
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

agent = Agent(
    "gemini-2.0-flash",
    instructions="""
You are a university directory lookup assistant. When given a person's name:

1. Search the web for their official university profile
2. Look for: Full name, Department, Building/Office location, Room number
3. Return ONLY information from official university sources

Return your findings as JSON with: name, department, building, room
If you cannot find the person, return: {{"status": "not_found"}}
""",
    result_type=OCRResult,  
    capabilities=[
        Thinking(),
        WebSearch(local="duckduckgo")
    ]
)

async def use_AI_agent(candidates: list[str], university: str) -> OCRResult:
    """Use LLM agent to find person via web search"""
    ocr_prompt = f"Find {', '.join(candidates)} at {university}..."
    
    try:
        result = await agent.run(ocr_prompt)
        # result is now a UniversityPerson object
        
        if not result or not result.name:
            logger.info("Agent did not find a match")
            return OCRResult()
        
        # Insert to database
        state.db.upsertPerson(result)
        
        logger.info("Agent found person: %s", result)
        return OCRResult(**result.model_dump())
        
    except Exception as e:
        logger.error("Agent lookup failed: %s", e, exc_info=True)
        return OCRResult()