import requests

url = "https://www.bok.or.kr/portal/bbs/B0000238/list.do?menuNo=200687"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
response = requests.get(url, headers=headers, timeout=20)
response.encoding = response.apparent_encoding
with open("C:/Users/infomax/Desktop/dev/duck/Reports/scratch/response.html", "w", encoding="utf-8") as f:
    f.write(response.text)
print("Saved HTML to response.html")
