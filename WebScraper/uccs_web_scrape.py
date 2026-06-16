from asyncio.log import logger

import requests
from bs4 import BeautifulSoup
import re
import json

async def main():
    import asyncpg
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    from dotenv import load_dotenv
    import os

    # load_dotenv()

    # DB_USER = os.getenv("DB_USER")
    # DB_PASSWORD = os.getenv("DB_PASSWORD")
    # DB_HOST = os.getenv("DB_HOST")
    # DB_NAME = os.getenv("DB_NAME")

    # try:
    #     pool = await asyncpg.create_pool(
    #         user=DB_USER,
    #         password=DB_PASSWORD,
    #         database=DB_NAME,
    #         host=DB_HOST,
    #         port=6543,
    #         statement_cache_size=0
    #     )          
    #     logger.info("Connected to database — host=%s | db=%s", DB_HOST, DB_NAME)
    # except Exception as e:
    #     logger.exception("Database connection pool failed — host=%s | db=%s | error: %s", DB_HOST, DB_NAME, e)
    #     raise

    # Fetch the webpage
    urls = [['https://phonedir.uccs.edu/employees?search=Polly%20Knuston', '', 'get-info']]
    '''
    urls = [["https://phonedir.uccs.edu/department/125953", "GOCA", "phone"],
           ["https://phonedir.uccs.edu/department/125955", "Graduate Studies", "phone"],
           ["https://phonedir.uccs.edu/department/126051", "Human Resources", "phone"],
           ["https://phonedir.uccs.edu/department/125958", "IT", "phone"],
           ["https://phonedir.uccs.edu/department/126026", "WEST", "phone"],
           ["https://phonedir.uccs.edu/department/126147", "Wellness Center", "phone"],
           ["https://phonedir.uccs.edu/department/126020", "VAPA", "phone"],
           ["https://phonedir.uccs.edu/department/126079", "Alumni Relations", "phone"],
           ["https://phonedir.uccs.edu/department/126135", "Development", "phone"],
           ["https://phonedir.uccs.edu/department/126043", "Lane Center 3rd Floor", "phone"],
           ["https://phonedir.uccs.edu/department/126014", "Theatreworks", "phone"],
           ["https://phonedir.uccs.edu/department/126003", "Sociology", "phone"],
           ["https://phonedir.uccs.edu/department/126000", "Science Center", "phone"],
           ["https://phonedir.uccs.edu/department/126068", "Registrar's Office", "phone"],
           ["https://phonedir.uccs.edu/department/125996", "Recreation Center", "phone"],
           ["https://phonedir.uccs.edu/department/126002", "Public Safety", "phone"],
           ["https://phonedir.uccs.edu/department/125988", "Psychology", "phone"],
           ["https://phonedir.uccs.edu/department/126106", "Provost's Office", "phone"],
           ["https://phonedir.uccs.edu/department/125985", "Political Science", "phone"],
           ["https://phonedir.uccs.edu/department/125984", "Physics", "phone"],
           ["https://phonedir.uccs.edu/department/125980", "Philosophy", "phone"],
           ["https://phonedir.uccs.edu/department/125979", "DPS", "phone"],
           ["https://phonedir.uccs.edu/department/125974", "MAE", "phone"],
           ["https://phonedir.uccs.edu/department/125973", "Mathematics", "phone"],
           ["https://phonedir.uccs.edu/department/125970", "Library", "phone"],
           ["https://phonedir.uccs.edu/department/125968", "LAS", "phone"]]
    urls = [["https://phonedir.uccs.edu/department/125902", "Anthropology", "phone"],
           ["https://phonedir.uccs.edu/department/126174", "Bachelor of Innovation", "phone"],
           ["https://phonedir.uccs.edu/department/126055", "Biofrontiers", "phone"],
           ["https://phonedir.uccs.edu/department/125907", "Biology", "phone"],
           ["https://phonedir.uccs.edu/department/125909", "Bookstore", "phone"],
           ["https://phonedir.uccs.edu/department/126091", "CLC", "phone"],
           ["https://phonedir.uccs.edu/department/125918", "Chancellor's Office", "phone"],
           ["https://phonedir.uccs.edu/department/125919", "Chemistry", "phone"],
           ["https://phonedir.uccs.edu/department/125894", "Controller's Office", "phone"],
           ["https://phonedir.uccs.edu/department/126066", "EPIIC", "phone"],
           ["https://phonedir.uccs.edu/department/125927", "Economics", "phone"],
           ["https://phonedir.uccs.edu/department/125932", "ECE", "phone"],
           ["https://phonedir.uccs.edu/department/125935", "English", "phone"],
           ["https://phonedir.uccs.edu/department/126201", "Ent Center", "phone"],
           ["https://phonedir.uccs.edu/department/125966", "Languages and Cultures", "phone"]
           ]
        ["https://comm.uccs.edu/directory", "Communications", "card"], 
        ["https://eas.uccs.edu/cs/directory", "Computer Science", "card"],
        ["https://eas.uccs.edu/ece/directory", "ECE", "card"], 
        ["https://eas.uccs.edu/departments/mechanical-and-aerospace-engineering/directory", "MAE", "card"],
        ["https://eas.uccs.edu/departments/deans-office-directory", "Dean of Engineering", "card"]
           '''
    for url, dept, scrape_type in urls:
        if scrape_type == "card":
            await card_directory_scrape(pool, url, dept)
        elif scrape_type == "phone":
            await phone_directory_scrape(pool, url, dept)
        elif scrape_type == "get-info":
            await get_directory_info(url)

    # await pool.close()


async def card_directory_scrape(pool, url, dept):
    response = requests.get(url)

    soup = BeautifulSoup(response.content, "html.parser")
    
    names = soup.find_all("div", class_="profile-page_contact_name")
    for name in names:
        name = name.text.strip()
        if ',' in name:
            name = name.split(',')[0] 
        if '.' in name:
            name = name.replace('.', '')  
        print(name.strip())
        if not await check_person_exists(pool, name):        
            await insert_person(pool, name.text.strip().upper(), dept)


async def get_directory_info(url):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        print(f"Scraping URL: {url} for directory info")
        browser = await p.chromium.launch(headless=True)

        page = await browser.new_page()

        await page.goto(url)

        await page.wait_for_timeout(5000)

        html = await page.content()

        soup = BeautifulSoup(html, "html.parser")
        app = soup.find("div", id="app")

        data = json.loads(app["data-page"])

        employee = data["props"]["employees"]["data"][0]
        print(employee)

        name = employee["name"]
        name = name.split(",")[1].strip() + " " + name.split(",")[0].strip()  # Reorder to "First Last"
        department = employee["department"]["dept_name"]

        print(name, department)

        await browser.close()

async def phone_directory_scrape(pool, url, dept):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        print(f"Scraping URL: {url} for department: {dept}")
        browser = await p.chromium.launch(headless=True)

        page = await browser.new_page()

        await page.goto(url)

        await page.wait_for_timeout(5000)

        html = await page.content()

        soup = BeautifulSoup(html, "html.parser")

        span = soup.select(
            "span.font-medium.text-gray-900.whitespace-nowrap"
        )

        for text in span:
            if ',' not in text.text:
                continue  # Skip if the expected format is not found
            split_text = text.text.strip().split(',')
            name = split_text[1].strip() + " " + split_text[0].strip()  # Reorder to "First Last"
            if not await check_person_exists(pool, name):
                await insert_person(pool, name.upper(), dept)
        
            print(name)



        await browser.close()

async def insert_person(pool, name, department):
    try:
        async with pool.acquire() as connection:
            await connection.execute("""
                INSERT INTO person (name, department, school)
                VALUES ($1, $2, $3)
            """, name, department, "UCCS")
    except Exception as e:
        logger.exception("Database insert failed — name=%s | department=%s | error: %s", name, department, e)
        raise

async def check_person_exists(pool, name):
    try:
        async with pool.acquire() as connection:
            row = await connection.fetchrow("""
                SELECT id FROM person
                WHERE UPPER(name) = UPPER($1)
            """, name)
            return row is not None
    except Exception as e:
        logger.exception("Database lookup failed — name=%s | error: %s", name, e)
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
