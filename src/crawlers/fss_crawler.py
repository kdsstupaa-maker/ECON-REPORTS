import datetime
import urllib.parse
from bs4 import BeautifulSoup
import requests
from src.crawlers.base_crawler import BaseCrawler

class FSSCrawler(BaseCrawler):
    def fetch_latest_reports(self):
        url = "https://www.fss.or.kr/fss/bbs/B0000188/list.do?menuNo=200218"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        reports = []
        try:
            response = requests.get(url, headers=headers, timeout=20, verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser", from_encoding="utf-8")
            
            # Common table structure in Korean government sites is table.board-list > tbody > tr
            tbody = soup.find("tbody")
            if not tbody:
                return reports
                
            rows = tbody.find_all("tr")
            for row in rows[:10]: # Look at first 10 rows
                title_tag = row.find("a")
                if not title_tag:
                    continue
                    
                title = title_tag.text.strip()
                if not title:
                    continue
                    
                href = title_tag.get("href", "")
                link = urllib.parse.urljoin("https://www.fss.or.kr", href)
                
                # Try to extract date
                date_td = row.find_all("td", class_="date")
                date_str = datetime.date.today().isoformat()
                if date_td:
                    date_str = date_td[0].text.strip()
                else:
                    # fallback to any td that matches yyyy-mm-dd
                    for td in row.find_all("td"):
                        txt = td.text.strip()
                        if len(txt) == 10 and txt.count("-") == 2:
                            date_str = txt
                            break
                            
                key = f"fss_{hash(link) % 10000000}"
                
                reports.append({
                    "key": key,
                    "title": title,
                    "pdf_url": link,
                    "author": "금융감독원",
                    "date": date_str
                })
        except Exception as e:
            print(f"[FSS] Crawler error: {e}")
            
        return reports
