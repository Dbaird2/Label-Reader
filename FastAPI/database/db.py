import asyncpg
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        from dotenv import load_dotenv
        import os

        load_dotenv()

        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST")
        DB_NAME = os.getenv("DB_NAME")

        try:
            self.pool = await asyncpg.create_pool(
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                host=DB_HOST,
                port=6543,
                statement_cache_size=0
            )          
            logger.info("Connected to database — host=%s | db=%s", DB_HOST, DB_NAME)
        except Exception as e:
            logger.exception("Database connection pool failed — host=%s | db=%s | error: %s", DB_HOST, DB_NAME, e)
            raise

    # async def upsertUser(self, email: str, name: str):
    #     try:
    #         await self.pool.execute('''
    #             INSERT INTO users (email, name) VALUES ($1, $2)
    #             ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name
    #         ''', email, name)
    #     except Exception as e:
    #         logger.exception("upsertUser failed — email=%s | error: %s", email, e)
    #         raise

    async def execute(self, query: str, *args):
        try:
            async with self.pool.acquire() as connection:
                return await connection.execute(query, *args)
        except Exception as e:
            logger.exception("Database execute failed — query=%s | args=%s | error: %s", query, args, e)
            raise

    async def lookupName(self, name: str):
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT name, building, room, department,
                        similarity(UPPER(name), UPPER($1)) AS score
                    FROM person
                    WHERE similarity(UPPER(name), UPPER($1)) > 0.5
                    ORDER BY score DESC
                LIMIT 1
            """, name)

            if not row:
                return None

            return {
                "name": row["name"],
                "building": row["building"],
                "room": row["room"],
                "department": row["department"],
                "confidence": float(row["score"])
            }
        except Exception as e:
            logger.exception("lookup_name failed — name=%s | error: %s", name, e)
            raise

    async def closeConnection(self):
        await self.pool.close()
