import urllib.parse
from bs4 import BeautifulSoup
import requests
from src.crawlers.base_crawler import BaseCrawler

class BOKCrawler(BaseCrawler):
    def fetch_latest_reports(self):
        # BOK경제연구 게시판
        url = "https://www.bok.or.kr/portal/bbs/B0000020/list.do?menuNo=200021"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        reports = []
        
        # 게시글 리스트 추출 (한국은행 전형적인 테이블/리스트 파싱)
        table = soup.find("div", class_="bdList")
        if not table:
            return reports
            
        items = table.find_all("li")
        for item in items:
            title_el = item.find("span", class_="titles")
            if not title_el:
                continue
            
            title = title_el.text.strip()
            
            # 링크와 고유 키 파싱
            link_el = item.find("a")
            href = link_el["href"] if link_el else ""
            # 예: /portal/bbs/B0000020/view.do?nttId=10065432&menuNo=200021
            parsed_url = urllib.parse.urlparse(href)
            params = urllib.parse.parse_qs(parsed_url.query)
            ntt_id = params.get("nttId", [""])[0]
            
            if not ntt_id:
                continue
                
            key = f"bok_{ntt_id}"
            
            # 첨부파일 다운로드 링크 파싱 (첫 번째 PDF 첨부물)
            pdf_url = f"https://www.bok.or.kr/portal/bbs/B0000020/fileCmd.do?fileSeq=1&nttId={ntt_id}"
            
            date_el = item.find("span", class_="date")
            date = date_el.text.strip() if date_el else ""
            
            reports.append({
                "key": key,
                "title": title,
                "pdf_url": pdf_url,
                "author": "한국은행 경제연구원",
                "date": date
            })
        
        return reports[:5] # 최신 5개만 반환
