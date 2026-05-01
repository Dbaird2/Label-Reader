import state
import pandas as pd
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

async def repeatInsert():

    logger.info("repeatInsert loop started")

    while True:
        # Fetch items and broadcast to WebSocket clients
        # try:
        #     await fetchAndBroadcastItems()
        # except Exception as e:
        #     logger.exception("Failed to build item list from DB rows: %s", e)
        
        # # Recalculate event impacts and broadcast to dashboard clients
        # try:
        #     await recalEventImpact()
        # except Exception as e:
        #     logger.exception("Scheduled impact update failed: %s", e)
        
        # # Check for recent drops and send Discord message if any
        # try:
        #     await recentDropsCheck()
        # except Exception as e:
        #     logger.exception("Recent Drops failed in main.py failed: %s", e)
        
        # # Update predicted prices for all items in the background
        # try:
        #     await updatePredictions()
        # except Exception as e:
        #     logger.exception("Background predicted price update failed: %s", e)
            
        await asyncio.sleep(3600)




