import requests
from bs4 import BeautifulSoup

url = "https://www.bok.or.kr/portal/bbs/B0000245/list.do?menuNo=200767"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
response = requests.get(url, headers=headers, timeout=20)
print("Status Code:", response.status_code)
print("Apparent Encoding:", response.apparent_encoding)
response.encoding = response.apparent_encoding

soup = BeautifulSoup(response.text, "html.parser")
print("Title of page:", soup.title.text.strip() if soup.title else "No title")

# Let's search for divs with list or board
print("\n--- Listing board list divs ---")
for div in soup.find_all("div", class_=True):
    classes = div.get("class")
    if "bdList" in classes or any("list" in c.lower() for c in classes) or any("board" in c.lower() for c in classes):
        print("Found div class:", classes, "id:", div.get("id"))

table = soup.find("div", class_="bdList")
if table:
    print("Found bdList!")
    items = table.find_all("li")
    print("Found items count:", len(items))
    for idx, item in enumerate(items[:3]):
        print(f"\n--- Item {idx} ---")
        print(item.prettify()[:1000])
else:
    print("bdList not found.")
