import datetime
import urllib.parse
from bs4 import BeautifulSoup
import requests
from src.crawlers.base_crawler import BaseCrawler

class KIETCrawler(BaseCrawler):
    def fetch_latest_reports(self):
        url = "https://www.kiet.re.kr/research/issueList"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        reports = []
        try:
            response = requests.get(url, headers=headers, timeout=20, verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser", from_encoding="utf-8")
            
            list_container = soup.find("ul", class_="list_box")
            if not list_container:
                return reports
                
            items = list_container.find_all("li", class_="item")
            
            for item in items[:10]: # Check up to 10 items
                title_tag = item.find("div", class_="rpt_tit").find("a")
                if not title_tag:
                    continue
                title = title_tag.text.strip()
                if not title:
                    continue
                    
                href = title_tag.get("href", "")
                link = urllib.parse.urljoin("https://www.kiet.re.kr", href)
                
                date_span = item.find("span", class_="date")
                if date_span:
                    date_str = date_span.text.strip().replace(".", "-")
                else:
                    date_str = datetime.date.today().isoformat()
                
                key = f"kiet_{hash(link) % 10000000}"
                
                reports.append({
                    "key": key,
                    "title": title,
                    "pdf_url": link,
                    "author": "산업연구원",
                    "date": date_str
                })
        except Exception as e:
            print(f"[KIET] Crawler error: {e}")
            
        return reports
