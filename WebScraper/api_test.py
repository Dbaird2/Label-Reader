import requests

r = requests.get("https://phonedir.uccs.edu/api/employees?search=Casi%20Frazier")
print(r.status_code)
data = r.json()
print(data)
data = data.get("data", [])
for person in data:
    name = person["name"]
    name = name.split(",")[1].strip() + " " + name.split(",")[0].strip()  
    print(name, ',', person["department"]["dept_name"])

# r = requests.get("https://phonedir.uccs.edu/api/departments")
# print(r.status_code)
# data = r.json()
# data = data.get("data", [])
# print(data  )
# for dept in data:
#     print(dept["dept_name"])