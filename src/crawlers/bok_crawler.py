import urllib.parse
from bs4 import BeautifulSoup
import requests
from src.crawlers.base_crawler import BaseCrawler

class BOKCrawler(BaseCrawler):
    def fetch_latest_reports(self):
        # BOK경제연구 게시판 (IMER)
        url = "https://www.bok.or.kr/imer/bbs/P0002456/list.do?menuNo=500789"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        reports = []
        
        # 게시글 리스트 추출 (한국은행 전형적인 테이블/리스트 파싱)
        bd_line = soup.select("div.bd-line > ul > li")
        for item in bd_line:
            title_el = item.find("a", class_="title")
            if not title_el:
                continue
            
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            
            # 링크와 고유 키 파싱
            parsed_url = urllib.parse.urlparse(href)
            params = urllib.parse.parse_qs(parsed_url.query)
            ntt_id = params.get("nttId", [""])[0]
            
            if not ntt_id:
                continue
                
            key = f"bok_{ntt_id}"
            
            # 첨부파일 다운로드 링크 파싱
            pdf_url = ""
            file_box = item.find("div", class_="fileGoupBox")
            if file_box:
                downloads = file_box.find_all("a", class_="i-download")
                for dl in downloads:
                    dl_href = dl.get("href", "")
                    if dl_href and ".pdf" in dl_href:
                        pdf_url = "https://www.bok.or.kr" + dl_href
                        break
            
            # 작성일 파싱
            date_el = item.find("span", class_="date")
            date = ""
            if date_el:
                hidden_el = date_el.find("span", class_="hidden")
                if hidden_el:
                    hidden_el.decompose()
                date = date_el.get_text(strip=True)
            
            reports.append({
                "key": key,
                "title": title,
                "pdf_url": pdf_url,
                "author": "한국은행 경제연구원",
                "date": date
            })
        
        return reports[:5] # 최신 5개만 반환
