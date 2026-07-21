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
    {"name": "한국은행", "list_url": "https://www.bok.or.kr/portal/singl/newsData/list.do?menuNo=201263"},
    {"name": "한국은행", "list_url": "https://www.bok.or.kr/portal/singl/newsData/list.do?menuNo=201156"},
    {"name": "한국은행", "list_url": "https://www.bok.or.kr/portal/singl/newsData/list.do?menuNo=200433"},
    {"name": "한국은행", "list_url": "https://www.bok.or.kr/portal/singl/newsData/list.do?menuNo=201265"},
    {"name": "국제금융센터", "list_url": "https://www.kcif.or.kr/front/board/boardList.do?intSection1=1&intSection2=1"},
    {"name": "산업연구원(동향분석)", "list_url": "https://www.kiet.re.kr/research/issueList"},
    {"name": "산업연구원(연구보고서)", "list_url": "https://www.kiet.re.kr/research/reportList"},
    {"name": "금융감독원", "list_url": "https://www.fss.or.kr/fss/bbs/B0000188/list.do?menuNo=200218"},
    {"name": "KDI(KDI Focus)", "list_url": "https://www.kdi.re.kr/research/focus"},
    {"name": "KDI(연구보고서)", "list_url": "https://www.kdi.re.kr/research/reportList"},
    {"name": "IMF", "list_url": "https://www.imf.org/en/Publications/Search?series=IMF+Working+Papers"}
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
        
    try:
        res = requests.get(url, headers=HEADERS, stream=True, timeout=20, verify=False)
        content_type = res.headers.get('Content-Type', '').lower()
        
        if 'text/html' in content_type:
            # HTML 응답이면 파일이 아님
            return
            
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        ext = ".pdf"
        if title.lower().endswith(".hwp"):
            ext = ".hwp"
        elif title.lower().endswith(".hwpx"):
            ext = ".hwpx"
        elif title.lower().endswith(".doc"):
            ext = ".doc"
        elif title.lower().endswith(".docx"):
            ext = ".docx"
        
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
            # networkidle 타임아웃 시 domcontentloaded로 재시도
            page.goto(list_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3) # 추가 대기
        
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        a_tags = soup.find_all('a', href=True)
        processed_hrefs = set()
        
        for a_tag in a_tags:
            href = a_tag['href']
            title = a_tag.get_text(strip=True)
            
            if len(title) < 8 or href == "#" or "javascript:void" in href.lower():
                continue
                
            if href in processed_hrefs:
                continue
            processed_hrefs.add(href)
            
            link = urllib.parse.urljoin(list_url, href)
            
            date_str = "1970-01-01" # 기본값을 아주 옛날로 설정하여 날짜를 못 찾으면 스킵하게 함
            
            date_str = "1970-01-01" # 기본값을 아주 옛날로 설정하여 날짜를 못 찾으면 스킵하게 함
            parent = a_tag.parent
            for _ in range(6):
                if not parent or parent.name == 'body': break
                txt = parent.get_text(separator=' ', strip=True)
                
                # YYYY-MM-DD, YYYY.MM.DD, YYYY. M. D. 등 모두 매칭
                match = re.search(r'202[0-9][-\.\s]+[0-1]?[0-9][-\.\s]+[0-3]?[0-9]', txt)
                if match:
                    clean = re.sub(r'[-\.\s]+', '-', match.group(0).strip('-.'))
                    parts = clean.split('-')
                    if len(parts) == 3:
                        date_str = f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                    else:
                        date_str = clean
                    break
                else:
                    # IMF 등의 영문 날짜 (July 16, 2026) 매칭
                    match_en = re.search(r'([A-Za-z]{3,9})\s+(\d{1,2}),\s+(202[0-9])', txt)
                    if match_en:
                        month_str, day, year = match_en.groups()
                        try:
                            month = datetime.strptime(month_str[:3], '%b').month
                            date_str = f"{year}-{month:02d}-{int(day):02d}"
                            break
                        except:
                            pass
                parent = parent.parent
                    
            if not is_recent(date_str):
                continue
                
            print(f"DEBUG: Found recent link {title} {date_str} {link}")
            
            try:
                if 'javascript:' in link.lower():
                    continue
                    
                # 리스트 페이지에 첨부파일이 직접 연결된 경우 (금감원 등)
                if 'filedown' in link.lower() or '.pdf' in link.lower() or '.hwp' in link.lower():
                    clean_att_text = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', title)
                    if not clean_att_text.lower().endswith('.pdf') and not clean_att_text.lower().endswith('.hwp') and not clean_att_text.lower().endswith('.hwpx'):
                        clean_att_text += ".pdf"
                    final_title = f"[{inst_name}] {clean_att_text}"
                    download_file(link, inst_name, final_title, date_str, data_list, existing_urls)
                    continue

                # 별도 request로 상세페이지 조회
                detail_res = requests.get(link, headers=HEADERS, timeout=10, verify=False)
                detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
                
                # 일반 첨부파일 링크 탐색
                att_links = detail_soup.find_all('a', href=True)
                downloaded_any = False
                for att in att_links:
                    att_href = att['href'].lower()
                    att_text = att.get_text(strip=True)
                    if '.pdf' in att_href or ('download' in att_href and 'pdf' in att_text.lower()) or 'filedown' in att_href:
                        if 'javascript:' in att_href: continue
                        
                        file_url = urllib.parse.urljoin(link, att['href'])
                        
                        # 첨부파일 이름 추출하여 중복 방지
                        if not att_text or len(att_text) < 3:
                            att_text = f"att_{len(existing_urls)}"
                            
                        # 금감원 등에서 확장자가 없을 경우 추가 (HWP는 제외)
                        if not att_text.lower().endswith('.pdf') and not att_text.lower().endswith('.hwp') and not att_text.lower().endswith('.hwpx'):
                            att_text += ".pdf"
                            
                        clean_att_text = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', att_text)
                        final_title = f"[{inst_name}] {title} - {clean_att_text}"
                        
                        download_file(file_url, inst_name, final_title, date_str, data_list, existing_urls)
                        downloaded_any = True
                
                # 국제금융센터: reportdownload JS 함수에서 fno 추출하여 직접 다운로드
                if not downloaded_any and 'kcif.or.kr' in link:
                    for btn in detail_soup.find_all(attrs={'onclick': True}):
                        onclick = btn.get('onclick', '')
                        match_fno = re.search(r"reportdownload\('([^']+)'\)", onclick)
                        if match_fno:
                            fno = match_fno.group(1)
                            pdf_url = f"https://www.kcif.or.kr/common/file/reportFileDownload?atch_no={fno}&lang=KR"
                            btn_title = btn.get('title', '') or title
                            if not btn_title.lower().endswith('.pdf'):
                                btn_title += '.pdf'
                            clean_title = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', btn_title)
                            final_title = f"[{inst_name}] {title} - {clean_title}"
                            download_file(pdf_url, inst_name, final_title, date_str, data_list, existing_urls)
                            downloaded_any = True
                            break  # 보통 첫 번째 파일이 메인 PDF

            except Exception as e:
                print(f"DEBUG: Exception in detail parsing: {e}")
                pass
                
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
