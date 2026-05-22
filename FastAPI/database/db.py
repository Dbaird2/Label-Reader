from models.OCR_Model import AddPersonModel, EditPersonModel
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
                    SELECT name, building, room, department, id, school,
                        similarity(UPPER(name), UPPER($1)) AS score
                    FROM person
                    WHERE similarity(UPPER(name), UPPER($1)) > 0.3
                    ORDER BY score DESC
                LIMIT 1
            """, name)

            if not row:
                return None

            return {
                "id": row["id"],
                "name": row["name"],
                "building": row["building"],
                "room": row["room"],
                "department": row["department"],
                "school": row["school"],
                "confidence": float(row["score"])
            }
        except Exception as e:
            logger.exception("lookup_name failed — name=%s | error: %s", name, e)
            raise
    
    async def upsertPerson(self, data: AddPersonModel):
        name = building = room = department = school = None  # initialize first

        try:
            name = data.name
            name = name.strip().upper() if name else None

            building = data.building
            building = building.strip().title() if building else None

            room = data.room
            room = room.strip().title() if room else None

            department = data.department
            department = department.strip().title() if department else None

            school = data.school
            school = school.strip().upper() if school else None

            if not name or not school or not department:
                logger.warning("upsertPerson called with missing required fields — payload: %s", data)
                raise ValueError("Fields missing that are required")

            await self.pool.execute('''
                INSERT INTO person (name, building, room, department, school) 
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (name, building, room, school) DO UPDATE 
                SET building = EXCLUDED.building,
                    room = EXCLUDED.room,
                    department = EXCLUDED.department
                ''', name, building, room, department, school)
            logger.info("Upserted person: %s", data.name)
        except Exception as e:
            logger.exception("upsertPerson failed — name=%s | error: %s", name, e)
            raise

    async def editPerson(self, data: EditPersonModel):
        name = building = room = department = school = None  # initialize first

        try:
            name = data.name
            name = name.strip().upper() if name else None

            building = data.building
            building = building.strip().title() if building else None

            room = data.room
            room = room.strip().title() if room else None

            department = data.department
            department = department.strip().title() if department else None

            school = data.school
            school = school.strip().upper() if school else None

            if not name or not school or not department:
                logger.warning("editPerson called with missing required fields — payload: %s", data)
                raise ValueError("Fields missing that are required")

            await self.pool.execute('''
                UPDATE person 
                SET name = $1,
                    building = $2,
                    room = $3,
                    department = $4
                WHERE id = $5 AND school = $6
                ''', name, building, room, department, data.id, school)
            logger.info("Edited person: %s", data.name)
        except Exception as e:
            logger.exception("editPerson failed — name=%s | error: %s", name, e)
            raise

    async def closeConnection(self):
        await self.pool.close()
