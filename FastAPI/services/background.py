import state
import asyncio
import logging

logger = logging.getLogger(__name__)

async def repeatInsert():

    logger.info("repeatInsert loop started")

    while True:
        await asyncio.sleep(360000)




