import asyncio

from pydantic_ai import Agent, RunContext
import state
from models.OCR_Model import  AddPersonModel
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
