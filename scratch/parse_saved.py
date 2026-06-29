from bs4 import BeautifulSoup

with open("C:/Users/infomax/Desktop/dev/duck/Reports/scratch/response.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
print("Page Title:", soup.title.text.strip() if soup.title else "No Title")

print("\n--- Any lists or tables? ---")
tables = soup.find_all("table")
print("Tables count:", len(tables))
for i, t in enumerate(tables):
    print(f"Table {i} class:", t.get("class"))

lists = soup.find_all("ul")
print("UL count:", len(lists))
for i, l in enumerate(lists[:15]):
    print(f"UL {i} class:", l.get("class"))

divs_with_list = [d for d in soup.find_all("div") if d.get("class") and any("list" in c.lower() or "board" in c.lower() for c in d.get("class"))]
print("Divs with list/board in class:", len(divs_with_list))
for d in divs_with_list[:10]:
    print("Div class:", d.get("class"), "id:", d.get("id"))

# Check if there is an alert or content-commingsoon
coming_soon = soup.find(class_="content-commingsoon")
if coming_soon:
    print("Found content-commingsoon:", coming_soon.get_text().strip())
