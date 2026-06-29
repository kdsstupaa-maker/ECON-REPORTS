import datetime
import urllib.parse
import re
from bs4 import BeautifulSoup
import requests
from src.crawlers.base_crawler import BaseCrawler

class KDICrawler(BaseCrawler):
    def fetch_latest_reports(self):
        url = "https://www.kdi.re.kr/research/focusList"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser", from_encoding="utf-8")
        reports = []
        
        list_group = soup.find("div", class_="page_list-group")
        if not list_group:
            return reports
            
        ul = list_group.find("ul")
        if not ul:
            return reports
            
        items = ul.find_all("li", recursive=False)
        for item in items:
            if len(reports) >= 5:
                break
            tit_el = item.find("div", class_="rpt_tit")
            if not tit_el:
                continue
            strong = tit_el.find("strong")
            if not strong:
                continue
            title = strong.text.strip()
            
            # Parse pub_no
            link_el = item.find("a")
            if not link_el or "href" not in link_el.attrs:
                continue
            href = link_el["href"]
            parsed_url = urllib.parse.urlparse(href)
            params = urllib.parse.parse_qs(parsed_url.query)
            pub_no = params.get("pub_no", [""])[0]
            if not pub_no:
                continue
                
            key = f"kdi_{pub_no}"
            
            # Parse PDF download link from onclick of button.i02
            btn = item.find("button", class_="i02")
            if not btn or "onclick" not in btn.attrs:
                continue
            onclick_val = btn["onclick"]
            match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", onclick_val)
            if not match:
                continue
            dl_href = match.group(1)
            pdf_url = urllib.parse.urljoin("https://www.kdi.re.kr", dl_href)
            
            # Parse author
            author = "KDI"
            other = item.find("div", class_="rpt_other")
            if other:
                p = other.find("p")
                if p:
                    spans = p.find_all("span")
                    if spans and len(spans) > 0:
                        author = spans[0].text.strip()
                        
            # Fetch detail page to get publication date
            detail_url = f"https://www.kdi.re.kr/research/focusView?pub_no={pub_no}"
            date = ""
            try:
                detail_resp = requests.get(detail_url, headers=headers, timeout=20)
                detail_resp.raise_for_status()
                detail_soup = BeautifulSoup(detail_resp.content, "html.parser", from_encoding="utf-8")
                top_wrap = detail_soup.find("div", class_="top_bg-wrap")
                if top_wrap:
                    title_tag = top_wrap.find("strong", class_="title")
                    if title_tag:
                        span_date = title_tag.find("span")
                        if span_date:
                            date = span_date.text.strip().rstrip(".").replace(".", "-")
            except Exception as e:
                print(f"[WARNING] Failed to fetch publication date for {key}: {e}")
                
            if not date:
                # fallback if not found
                date = datetime.date.today().isoformat()
                
            reports.append({
                "key": key,
                "title": title,
                "pdf_url": pdf_url,
                "author": author,
                "date": date
            })
            
        return reports
