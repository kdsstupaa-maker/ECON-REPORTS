import os
import json
import re
from datetime import datetime, timedelta
import urllib.parse
import hashlib
import time
import requests
from bs4 import BeautifulSoup
import holidays
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDFS_DIR = os.path.join(BASE_DIR, "pdfs")
DATA_FILE = os.path.join(BASE_DIR, "data", "reports.json")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

TARGET_SITES = [
    # === 한국은행 (보도자료, 조사연구, 이슈노트 등) ===
    {"name": "한국은행", "list_url": "https://www.bok.or.kr/portal/singl/newsData/list.do?menuNo=201263"},
    {"name": "한국은행", "list_url": "https://www.bok.or.kr/portal/singl/newsData/list.do?menuNo=201156"},
    {"name": "한국은행", "list_url": "https://www.bok.or.kr/portal/singl/newsData/list.do?menuNo=200433"},
    {"name": "한국은행", "list_url": "https://www.bok.or.kr/portal/singl/newsData/list.do?menuNo=201265"},
    # === 국제금융센터 ===
    {"name": "국제금융센터", "list_url": "https://www.kcif.or.kr/front/board/boardList.do?intSection1=1&intSection2=1"},
    # === 산업연구원 ===
    {"name": "산업연구원", "list_url": "https://www.kiet.re.kr/research/issueList"},
    {"name": "산업연구원", "list_url": "https://www.kiet.re.kr/research/reportList"},
    # === 금융감독원 ===
    {"name": "금융감독원", "list_url": "https://www.fss.or.kr/fss/bbs/B0000188/list.do?menuNo=200218"},
    # === KDI ===
    {"name": "KDI", "list_url": "https://www.kdi.re.kr/research/focus"},
    {"name": "KDI", "list_url": "https://www.kdi.re.kr/research/reportList"},
    # === IMF ===
    {"name": "IMF", "list_url": "https://www.imf.org/en/Publications/Search?series=IMF+Working+Papers"},
    # === 금융위원회 ===
    {"name": "금융위", "list_url": "https://www.fsc.go.kr/info/ntc_news_list"},
    # === 금융연구원 ===
    {"name": "금융연구원", "list_url": "https://www.kif.re.kr/kif2/research/director_report.aspx"},
    # === 자본시장연구원 ===
    {"name": "자본시장연구원", "list_url": "https://www.kcmi.re.kr/report/report_list"},
    # === 우리금융경영연구소 ===
    {"name": "우리금융경영연구소", "list_url": "https://www.woorifg.com/kor/research/report.do"},
    # === BIS ===
    {"name": "BIS", "list_url": "https://www.bis.org/doclist/papers.htm"},
    # === PIMCO ===
    {"name": "PIMCO", "list_url": "https://www.pimco.com/en-us/insights"},
    # === Fed San Francisco ===
    {"name": "Fed San Francisco", "list_url": "https://www.frbsf.org/research-and-insights/publications/economic-letter/"},
    # === 상공회의소 ===
    {"name": "상공회의소", "list_url": "https://www.korcham.net/nCham/Service/Economy/appl/KcciReportList.asp"},
    # === 현대경제연구원 ===
    {"name": "현대경제연구원", "list_url": "https://www.hri.co.kr/board/reportList.asp"},
    # === 부동산연구원 ===
    {"name": "부동산연구원", "list_url": "https://www.reb.or.kr/r-one/research/report.do"},
    # === 한국경영자총협회 ===
    {"name": "한국경영자협회", "list_url": "https://www.kefplaza.com/web/pages/gc415100.asp"},
    # === 조세재정연구원 ===
    {"name": "조세재정연", "list_url": "https://www.kipf.re.kr/cmm/fms/TotalFileDown.do"},
    # === 한국안보전략연구원 ===
    {"name": "한국안보전략연구원", "list_url": "https://www.inss.re.kr/publication/periodical.do"},
    # === OECD ===
    {"name": "OECD", "list_url": "https://www.oecd.org/en/publications.html"},
    # === 한국리츠협회 ===
    {"name": "한국리츠협회", "list_url": "https://www.kareit.or.kr/board/boardList.do"},
    # === 토지주택연구원 ===
    {"name": "토지주택연구원", "list_url": "https://www.krihs.re.kr/publica/reportList.do"},
    # === 무역협회국제무역통상연구원 ===
    {"name": "무역협회국제무역통상연구원", "list_url": "https://www.kita.net/cmmrcInfo/rsrchReprt/list.do"},
    # === 예금보험공사 ===
    {"name": "예금보험공사", "list_url": "https://www.kdic.or.kr/data/publication.do"},
    # === 주택산업연구원 ===
    {"name": "주택산업연구원", "list_url": "https://www.khi.re.kr/board_report"},
    # === 아산정책연구원 ===
    {"name": "아산정책연구원", "list_url": "https://www.asaninst.org/contents/"},
    # === 한신평 (한국신용평가) ===
    {"name": "한신평", "list_url": "https://www.kisrating.com/research/report.do"},
    # === kb금융연구소 ===
    {"name": "kb금융연구소", "list_url": "https://www.kbfg.com/kbresearch/report/reportList.do"},
    # === 하나금융연구소 ===
    {"name": "하나금융연구소", "list_url": "https://www.hanafn.com/research/researchMain.do"},
    # === 포스코경영연구원 ===
    {"name": "포스코경영연구원", "list_url": "https://www.posri.re.kr/ko/board/content/list?board_id=report"},
    # === 나이스신평 ===
    {"name": "나이스신평", "list_url": "https://www.nicerating.com/research/researchList.do"},
    # === BlackRock ===
    {"name": "BlackRock", "list_url": "https://www.blackrock.com/corporate/insights"},
    # === 대외경제정책연구원 ===
    {"name": "대외경제정책연구원", "list_url": "https://www.kiep.go.kr/gallery.es?mid=a10101000000"},
    # === 한기평 (한국기업평가) ===
    {"name": "한기평", "list_url": "https://www.korearatings.com/report/report_list.do"},
    # === Fed New York ===
    {"name": "Fed New York", "list_url": "https://www.newyorkfed.org/research"},
    # === 국회예산정책처 ===
    {"name": "국회예산정책보고서", "list_url": "https://www.nabo.go.kr/report/reportList.do"},
    # === 국가데이터처 ===
    {"name": "국가데이터처", "list_url": "https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardList.do?bbsId=BBSMSTR_000000000062"},
    # === 보험연구원 ===
    {"name": "보험연구원", "list_url": "https://www.kiri.or.kr/report/reportList.do"},
]

def get_cutoff_date(business_days_ago=2):
    kr_holidays = holidays.KR()
    date_cursor = datetime.now().date()
    days_subtracted = 0
    
    while days_subtracted < business_days_ago:
        date_cursor -= timedelta(days=1)
        if date_cursor.weekday() < 5 and date_cursor not in kr_holidays:
            days_subtracted += 1
            
    return datetime.combine(date_cursor, datetime.min.time())

def is_recent(date_str):
    if not date_str:
        return False
    try:
        clean_date = re.sub(r'[^0-9]', '', date_str)
        if len(clean_date) == 8:
            d = datetime.strptime(clean_date, "%Y%m%d")
            cutoff = get_cutoff_date(2)
            return d >= cutoff
    except:
        pass
    return False

def download_file(url, inst_name, title, date_str, data_list, existing_urls):
    if url in existing_urls:
        return
        
    # PDF만 허용하도록 파일명 체크
    if title.lower().endswith('.hwp') or title.lower().endswith('.hwpx') or title.lower().endswith('.doc') or title.lower().endswith('.docx'):
        print(f"Skipped non-PDF: {title}")
        return
        
    try:
        res = requests.get(url, headers=HEADERS, stream=True, timeout=20, verify=False)
        content_type = res.headers.get('Content-Type', '').lower()
        
        if 'text/html' in content_type:
            # HTML 응답이면 파일이 아님
            return
            
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        ext = ".pdf"
        
        filename = f"{inst_name}_{url_hash}{ext}"
        filepath = os.path.join(PDFS_DIR, filename)
        
        with open(filepath, 'wb') as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)
                
        data_list.append({
            "institution": inst_name,
            "title": title,
            "date": date_str,
            "filename": filename,
            "type": "PDF",
            "url": url,
            "downloaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        existing_urls.add(url)
        print(f"Downloaded: {title} ({inst_name})")
    except Exception as e:
        print(f"Download failed for {url}: {e}")

def scrape_generic_bbs(page, inst_name, list_url, data_list, existing_urls):
    print(f"Scraping {inst_name}...")
    try:
        try:
            page.goto(list_url, wait_until="networkidle", timeout=30000)
        except:
            page.goto(list_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        a_tags = soup.find_all('a', href=True)
        processed_hrefs = set()
        
        date_patterns = [
            r'202[0-9][-\.\s]+[0-1]?[0-9][-\.\s]+[0-3]?[0-9]',  # 2026-07-22, 2026.07.22
            r'202[0-9]\s*년\s*[0-1]?[0-9]\s*월\s*[0-3]?[0-9]\s*일',  # 2026년 7월 22일
            r'\b2[0-9][-\.\s]+[0-1]?[0-9][-\.\s]+[0-3]?[0-9]\b', # 26.07.22
            r'([A-Za-z]{3,9})\s+(\d{1,2}),\s+(202[0-9])' # Jul 22, 2026
        ]
        
        for a_tag in a_tags:
            href = a_tag['href']
            title = a_tag.get_text(strip=True)
            
            if len(title) < 8 or href == "#" or "javascript:void" in href.lower():
                continue
                
            if href in processed_hrefs:
                continue
            processed_hrefs.add(href)
            
            link = urllib.parse.urljoin(list_url, href)
            
            date_str = "1970-01-01"
            
            container = a_tag.find_parent(['tr', 'li', 'div', 'dl'])
            if not container:
                container = a_tag.parent
                
            txt = container.get_text(separator=' ', strip=True) if container else a_tag.get_text(separator=' ', strip=True)
            
            for pattern in date_patterns:
                match = re.search(pattern, txt)
                if match:
                    if '년' in match.group(0):
                        clean = re.sub(r'[^0-9]', '-', match.group(0))
                        clean = re.sub(r'-+', '-', clean).strip('-')
                        parts = clean.split('-')
                        if len(parts) >= 3:
                            date_str = f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                    elif re.search(r'[A-Za-z]', match.group(0)):
                        month_str, day, year = match.groups()
                        try:
                            month = datetime.strptime(month_str[:3], '%b').month
                            date_str = f"{year}-{month:02d}-{int(day):02d}"
                        except: pass
                    else:
                        clean = re.sub(r'[-\.\s]+', '-', match.group(0).strip('-.'))
                        parts = clean.split('-')
                        if len(parts) >= 3:
                            year = parts[0]
                            if len(year) == 2: year = "20" + year
                            date_str = f"{year}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                    if date_str != "1970-01-01":
                        break
                        
            if not is_recent(date_str):
                continue
                
            print(f"DEBUG: Found recent link {title} {date_str} {link}")
            
            try:
                if 'javascript:' in link.lower() and 'kcif' not in link:
                    continue
                    
                if 'filedown' in link.lower() or '.pdf' in link.lower() or 'download' in link.lower():
                    if '.hwp' in link.lower() or '.doc' in link.lower() or '.zip' in link.lower():
                        continue
                    clean_att_text = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', title)
                    if not clean_att_text.lower().endswith('.pdf'):
                        clean_att_text += ".pdf"
                    final_title = f"[{inst_name}] {clean_att_text}"
                    download_file(link, inst_name, final_title, date_str, data_list, existing_urls)
                    continue

                try:
                    page.goto(link, wait_until="domcontentloaded", timeout=15000)
                    time.sleep(2)
                    detail_html = page.content()
                    detail_soup = BeautifulSoup(detail_html, 'html.parser')
                except:
                    continue
                
                att_links = detail_soup.find_all('a', href=True)
                downloaded_any = False
                for att in att_links:
                    att_href = att['href'].lower()
                    att_text = att.get_text(strip=True)
                    
                    if '.hwp' in att_href or '.doc' in att_href or '.zip' in att_href:
                        continue
                    if '.hwp' in att_text.lower() or '.doc' in att_text.lower() or '.zip' in att_text.lower():
                        continue
                        
                    is_pdf_link = False
                    if '.pdf' in att_href or 'pdf' in att_text.lower():
                        is_pdf_link = True
                    elif 'filedown' in att_href or 'download' in att_href or '첨부' in att_text or '다운로드' in att_text:
                        is_pdf_link = True
                        
                    if is_pdf_link:
                        if 'javascript:' in att_href: continue
                        
                        file_url = urllib.parse.urljoin(link, att['href'])
                        if not att_text or len(att_text) < 3:
                            att_text = f"att_{len(existing_urls)}"
                            
                        if not att_text.lower().endswith('.pdf'):
                            att_text += ".pdf"
                            
                        clean_att_text = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', att_text)
                        final_title = f"[{inst_name}] {title} - {clean_att_text}"
                        
                        download_file(file_url, inst_name, final_title, date_str, data_list, existing_urls)
                        downloaded_any = True
                
                if not downloaded_any and 'kcif.or.kr' in link:
                    for btn in detail_soup.find_all(attrs={'onclick': True}):
                        onclick = btn.get('onclick', '')
                        match_fno = re.search(r"reportdownload\('([^']+)'\)", onclick)
                        if match_fno:
                            fno = match_fno.group(1)
                            pdf_url = f"https://www.kcif.or.kr/common/file/reportFileDownload?atch_no={fno}&lang=KR"
                            btn_title = btn.get('title', '') or title
                            if not btn_title.lower().endswith('.pdf'):
                                btn_title += ".pdf"
                            clean_title = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', btn_title)
                            final_title = f"[{inst_name}] {title} - {clean_title}"
                            download_file(pdf_url, inst_name, final_title, date_str, data_list, existing_urls)
                            downloaded_any = True
                            break
                            
                try: page.goto(list_url, wait_until="domcontentloaded", timeout=30000)
                except: pass
                time.sleep(1)

            except Exception as e:
                print(f"DEBUG: Exception in detail parsing: {e}")
                try: page.goto(list_url, wait_until="domcontentloaded", timeout=30000)
                except: pass
                
    except Exception as e:
        print(f"Error scraping {inst_name}: {e}")

def cleanup_old_files(data_list):
    current_time = datetime.now()
    cutoff_time = current_time - timedelta(days=7)
    
    new_data = []
    for item in data_list:
        try:
            downloaded_at = datetime.strptime(item.get("downloaded_at", ""), "%Y-%m-%d %H:%M:%S")
            if downloaded_at >= cutoff_time:
                new_data.append(item)
            else:
                filepath = os.path.join(PDFS_DIR, item['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"Deleted old file: {item['filename']}")
        except:
            new_data.append(item)
            
    return new_data

def run_scrapers():
    existing_urls = set()
    data_list = []
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
                for item in data_list:
                    if 'url' in item:
                        existing_urls.add(item['url'])
        except Exception as e:
            print(f"Error loading existing data: {e}")

    # Playwright를 이용해 동적 웹페이지 수집
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=HEADERS['User-Agent'], ignore_https_errors=True)
        page = context.new_page()
        
        for site in TARGET_SITES:
            scrape_generic_bbs(page, site['name'], site['list_url'], data_list, existing_urls)
            
        browser.close()
        
    data_list = cleanup_old_files(data_list)
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)
        
    print(f"Scraping completed. Total reports: {len(data_list)}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    run_scrapers()
