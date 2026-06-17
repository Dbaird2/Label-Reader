from urllib.parse import quote

import requests

# r = requests.get("https://phonedir.uccs.edu/api/employees?search=Casi%20Frazier")
# print(r.status_code)
# data = r.json()
# print(data)
# data = data.get("data", [])
# for person in data:
#     name = person["name"]
#     name = name.split(",")[1].strip() + " " + name.split(",")[0].strip()  
#     print(name, ',', person["department"]["dept_name"])

# r = requests.get("https://phonedir.uccs.edu/api/departments")
# print(r.status_code)
# data = r.json()
# data = data.get("data", [])
# print(data  )
# for dept in data:
#     print(dept["dept_name"])
async def test_phone_directory_scrape():
    try:
        from bs4 import BeautifulSoup
        from playwright.async_api import async_playwright
        from undetected_playwright import Malenia
        import json
        
        async with async_playwright() as p:
            query = "Polly Knutson"
            phonedir_url = f"https://phonedir.uccs.edu/employees?search={quote(query)}"
            browser = await p.chromium.launch(
                headless=True
            )
            context = await browser.new_context(
                locale="en-US"
            )

            await Malenia.apply_stealth(context)

            page = await context.new_page()
            await page.goto(phonedir_url, timeout=15000)
            
            try:
                await page.goto(phonedir_url, timeout=15000)
                await page.wait_for_timeout(6000)    

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                app = soup.find("div", id="app")
                
                if not app:
                    print("App div not found")
                    return '{"found": false}'
                data = json.loads(app["data-page"])
                employees = data.get("props", {}).get('employees', []).get("data", [])
                # print('Keys in data:', employees.keys())
                print("Employees found:", employees)
                if not employees:
                    return '{"found": false}'
                
                # Process first result
                employee = employees[0]
                name_parts = employee["name"].split(",")
                first_name = name_parts[1].strip()
                last_name = name_parts[0].strip()
                name = f"{first_name} {last_name}"
                
                department = employee.get("department", {}).get("dept_name", "")
                building = employee.get("building", "")
                room = employee.get("room", "")

                print(f"Found: {name}, Dept: {department}, Building: {building}, Room: {room}")
                
                

                
                
            finally:
                await browser.close()
    
    except Exception as e:
        return f"Error: {str(e)}"
    
if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_phone_directory_scrape())
    print(result)