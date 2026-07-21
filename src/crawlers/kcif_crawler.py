import re
import os
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin
from .base_crawler import BaseCrawler

logger = logging.getLogger("kcif_crawler")

class KCIFCrawler(BaseCrawler):
    def __init__(self, pdf_dir, kcif_id, kcif_pwd):
        super().__init__(pdf_dir)
        self.kcif_id = kcif_id
        self.kcif_pwd = kcif_pwd
        self.base_url = "https://www.kcif.or.kr"
        self.session = requests.Session()
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.base_url
        }
        self.session.headers.update(self.headers)
        self._login()

    def _login(self):
        if not self.kcif_id or not self.kcif_pwd:
            logger.warning("KCIF id/pwd not provided. Proceeding without login.")
            return

        login_url = urljoin(self.base_url, "/webUser/loginProc")
        payload = {
            "mem_id": self.kcif_id,
            "mem_pwd": self.kcif_pwd,
            "user_yn": "N",
            "email": ""
        }
        try:
            res = self.session.post(login_url, data=payload, verify=False, timeout=15)
            logger.info(f"KCIF login requested. Status: {res.status_code}")
        except Exception as e:
            logger.error(f"KCIF login failed: {e}")

    def fetch_latest_reports(self):
        reports = []
        endpoints = [
            "/analysis/analysisList",
            "/brief/briefList"
        ]
        
        for endpoint in endpoints:
            url = urljoin(self.base_url, endpoint)
            try:
                res = self.session.get(url, verify=False, timeout=15)
                res.encoding = 'utf-8'
                soup = BeautifulSoup(res.text, "html.parser")
            except Exception as e:
                logger.error(f"KCIF parsing error for {endpoint}: {e}")
                continue

            list_container = soup.find('ul', class_='page_list')
            if not list_container:
                list_container = soup.find('div', class_='page_list')
            
            if list_container:
                for li in list_container.find_all('li'):
                    title_elem = li.find('p', class_='lock') or li.find('a', class_='title')
                    if not title_elem:
                        continue
                    title = title_elem.text.strip()
                    
                    date_str = ""
                    date_match = re.search(r'\d{4}\.\d{2}\.\d{2}', li.text)
                    if date_match:
                        date_str = date_match.group(0).replace('.', '-')
                    
                    pdf_elem = li.find('a', attrs={"rpt_no": True})
                    if not pdf_elem:
                        continue
                    
                    rpt_no = pdf_elem.get("rpt_no")
                    
                    # Extact fno from onclick filePreview
                    # onclick="filePreview('...','...','pdf','260706.pdf','AHr4m6WIZWhVvoa7WmPE8w%3D%3D');"
                    onclick_str = pdf_elem.get("onclick", "")
                    fno = ""
                    parts = onclick_str.split("','")
                    if len(parts) >= 5:
                        fno = parts[4].replace("');", "")
                    
                    pdf_url = urljoin(self.base_url, f"/common/file/reportFileDownload?atch_no={fno}&lang=KR")
                    
                    reports.append({
                        "key": f"KCIF_{rpt_no}",
                        "title": title,
                        "pdf_url": pdf_url,
                        "author": "국제금융센터",
                        "date": date_str
                    })
        
        return reports

    def download_pdf(self, url, folder_name, filename):
        return super().download_pdf(url, folder_name, filename, session=self.session)
