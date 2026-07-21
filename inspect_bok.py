"""
BOK Ajax API 엔드포인트 직접 호출 테스트
실제 URL: /portal/singl/newsData/listCont.do
"""
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.bok.or.kr"
LIST_CONT_URL = f"{BASE_URL}/portal/singl/newsData/listCont.do"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html, */*; q=0.01",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE_URL}/portal/singl/newsData/list.do?menuNo=201150&sort=1&pageUnit=10",
}

# form 파라미터 (원본 페이지의 form#frm 파라미터 재현)
params = {
    "pageIndex": "1",
    "menuNo": "201150",
    "syncMenuChekKey": "1",
    "searchCnd": "1",
    "searchKwd": "",
    "sort": "1",
    "pageUnit": "10",
    "sdate": "",
    "edate": "",
}

print("=== BOK listCont.do API 호출 ===")
resp = requests.get(LIST_CONT_URL, params=params, headers=headers, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Encoding: {resp.encoding}")
print(f"Content-Type: {resp.headers.get('Content-Type')}")
print(f"Length: {len(resp.content)}")
print()

resp.encoding = "utf-8"
text = resp.text

# @@@숫자@@@ 패턴 확인 (BOK 사이트 특유의 총건수 마커)
import re
match = re.search(r'@@@(\d+)@@@', text)
if match:
    print(f"총 건수: {match.group(1)}")

# HTML 파싱
soup = BeautifulSoup(text, "lxml")

# bbsRowCls 다시 확인
rows = soup.find_all("li", class_="bbsRowCls")
print(f"bbsRowCls 행 수: {len(rows)}")

for i, row in enumerate(rows[:3]):
    print(f"\n=== 자료 #{i+1} ===")
    
    # 제목
    title_el = row.find("a", class_="title")
    title = title_el.get_text(strip=True) if title_el else "없음"
    onclick = title_el.get("onclick", "") if title_el else ""
    href = title_el.get("href", "") if title_el else ""
    print(f"  제목: {title[:60]}")
    print(f"  onclick: {onclick[:100]}")
    print(f"  href: {href}")
    
    # 날짜
    date_el = row.find("span", class_="date")
    if date_el:
        sr = date_el.find("span", class_="sr-only")
        if sr:
            sr.decompose()
        date_text = date_el.get_text(strip=True)
        print(f"  날짜: {date_text}")
    
    # 부서/카테고리
    depart_el = row.find("span", class_="depart")
    if depart_el:
        sr = depart_el.find("span", class_="sr-only")
        if sr:
            sr.decompose()
        print(f"  부서: {depart_el.get_text(strip=True)[:40]}")
    
    # Raw HTML
    print(f"\n  Raw HTML:\n{row.prettify()[:600]}")

# POST 방식도 시도
print()
print("=== POST 방식 시도 ===")
resp2 = requests.post(LIST_CONT_URL, data=params, headers=headers, timeout=30)
print(f"POST Status: {resp2.status_code}")
resp2.encoding = "utf-8"
rows2 = BeautifulSoup(resp2.text, "lxml").find_all("li", class_="bbsRowCls")
print(f"POST bbsRowCls 행 수: {len(rows2)}")
if rows2:
    title2 = rows2[0].find("a", class_="title")
    if title2:
        print(f"  첫 번째 제목: {title2.get_text(strip=True)[:60]}")
