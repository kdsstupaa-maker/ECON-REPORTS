import urllib.parse
from bs4 import BeautifulSoup
import requests
from src.crawlers.base_crawler import BaseCrawler

class BOKCrawler(BaseCrawler):
    def fetch_latest_reports(self):
        # 한국은행 뉴스/자료 게시판 (AJAX endpoint)
        url = "https://www.bok.or.kr/portal/singl/newsData/listCont.do"
        data = {'menuNo': '201150', 'sort': '1', 'pageUnit': '10', 'pageIndex': '1'}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        response = requests.post(url, data=data, headers=headers, timeout=20, verify=False)
        response.raise_for_status()
        
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        reports = []
        
        # 게시글 리스트 추출
        items = soup.select("div.bd-line > ul > li")
        for item in items:
            title_el = item.find("a", class_="title")
            if not title_el:
                continue
            
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            
            if not href:
                continue
                
            # 링크에서 고유 ID 파싱
            parsed_url = urllib.parse.urlparse(href)
            params = urllib.parse.parse_qs(parsed_url.query)
            ntt_id = params.get("nttId", [""])[0]
            
            if not ntt_id:
                continue
                
            key = f"bok_{ntt_id}"
            detail_url = urllib.parse.urljoin("https://www.bok.or.kr", href)
            
            # 상세 페이지로 이동하여 PDF 링크 추출
            pdf_url = ""
            try:
                detail_res = requests.get(detail_url, headers=headers, timeout=15, verify=False)
                detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                files = detail_soup.select(".file-set a.file")
                for f in files:
                    file_href = f.get("href", "")
                    if ".pdf" in file_href.lower():
                        pdf_url = urllib.parse.urljoin("https://www.bok.or.kr", file_href)
                        break
            except Exception as e:
                import logging
                logging.getLogger("bok_crawler").warning(f"Failed to fetch detail page for {key}: {e}")
            
            # Skip if there is no PDF url
            if not pdf_url:
                continue
            
            # 작성일 파싱
            date_el = item.find("span", class_="date")
            date_str = ""
            if date_el:
                sr_only_el = date_el.find("span", class_="sr-only")
                if sr_only_el:
                    sr_only_el.decompose()
                # Normalize date to YYYY-MM-DD format
                date_str = date_el.text.strip().replace(".", "-")
            
            reports.append({
                "key": key,
                "title": title,
                "pdf_url": pdf_url,
                "author": "한국은행",
                "date": date_str
            })
        
        return reports[:10]
