import requests
from bs4 import BeautifulSoup

urls = {
    "보도자료": "https://www.bok.or.kr/portal/bbs/B0000213/list.do?menuNo=200748",
    "의사록": "https://www.bok.or.kr/portal/bbs/B0000245/list.do?menuNo=200767",
    "공지사항": "https://www.bok.or.kr/portal/bbs/B0000227/list.do?menuNo=200765",
    "연설및강연": "https://www.bok.or.kr/portal/bbs/B0000225/list.do?menuNo=200773",
    "간행물": "https://www.bok.or.kr/portal/bbs/B0000238/list.do?menuNo=200687",
}

session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}
session.headers.update(headers)

print("Visiting main...")
session.get("https://www.bok.or.kr/portal/main/main.do", timeout=20)

for name, url in urls.items():
    print(f"\nTesting {name}: {url}")
    resp = session.get(url, timeout=20)
    print("  Status Code:", resp.status_code)
    print("  Length:", len(resp.text))
    if "잘못된 접근입니다" in resp.text:
        print("  Status: Invalid Access Alert")
        continue
    
    resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.title.text.strip() if soup.title else "No Title"
    print("  Title:", title)
    
    coming_soon = soup.find(class_="content-commingsoon")
    if coming_soon:
        print("  Status: Coming Soon")
        continue
        
    table = soup.find("div", class_="bdList")
    if table:
        print("  Status: Success! Found bdList")
        items = table.find_all("li")
        print(f"  Items found: {len(items)}")
        if items:
            print("  First item preview:")
            print(items[0].prettify()[:500])
    else:
        print("  Status: No bdList found")
        # Check any ul or table
        t = soup.find("table")
        if t:
            print("  Found a table!")
        else:
            # check body text
            print("  Body text preview:", soup.body.get_text().strip()[:200] if soup.body else "No body")
