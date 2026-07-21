import sys
import os
import logging
import json
from datetime import datetime, timedelta
import re

# Add project root to sys.path to support execution from any directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config_loader import Config
from src.db_manager import DBManager
from src.crawlers.bok_crawler import BOKCrawler
from src.crawlers.kdi_crawler import KDICrawler
from src.services.gemini_service import GeminiSummarizer
from src.services.outlook_service import OutlookService
from src.services.gmail_service import GmailService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main_runner")

from src.crawlers.kcif_crawler import KCIFCrawler

def run_agent():
    logger.info("Starting Financial Reports Monitoring Agent...")
    
    # 1. Load configuration
    try:
        config = Config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return

    # 2. Initialize Database
    try:
        db = DBManager(config.db_path)
        db.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    # 3. Initialize Services
    try:
        summarizer = GeminiSummarizer(api_key=config.gemini_key, model_name=config.gemini_model)
        outlook = OutlookService(recipient=config.email_recipient)
        
        if not getattr(config, 'gmail_sender', None) or not getattr(config, 'gmail_app_password', None):
            logger.error("Gmail configuration missing. Cannot send emails.")
            return
            
        gmail = GmailService(
            sender_email=config.gmail_sender,
            app_password=config.gmail_app_password,
            recipient=config.email_recipient
        )
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        return

    # 4. Initialize Crawlers
    crawlers = [
        ("한국은행", BOKCrawler(config.pdf_dir)),
        ("KDI", KDICrawler(config.pdf_dir)),
        ("국제금융센터", KCIFCrawler(config.pdf_dir, config.kcif_id, config.kcif_pwd))
    ]

    # Calculate target dates
    now = datetime.now()
    target_dates = [now.strftime("%Y-%m-%d"), (now - timedelta(days=1)).strftime("%Y-%m-%d")]
    
    if now.weekday() == 6:  # 일요일 (0:월, ..., 6:일)
        target_dates.append((now - timedelta(days=2)).strftime("%Y-%m-%d")) # 금요일
        # (토요일은 이미 days=1 로 target_dates 에 포함됨)
    elif now.weekday() == 0:  # 월요일 (기존 로직 유지)
        target_dates.append((now - timedelta(days=2)).strftime("%Y-%m-%d")) # Sat
        target_dates.append((now - timedelta(days=3)).strftime("%Y-%m-%d")) # Fri
        
    logger.info(f"Target dates for filtering: {target_dates}")

    # 5. Process Crawled Reports
    processed_reports = []
    summaries_for_dashboard = []
    attachment_paths = []

    for name, crawler in crawlers:
        logger.info(f"Fetching latest reports from {name}...")
        try:
            reports = crawler.fetch_latest_reports()
            logger.info(f"Found {len(reports)} reports from {name}")
        except Exception as e:
            logger.error(f"Failed to fetch reports from {name}: {e}")
            continue

        for r in reports:
            report_key = r["key"]
            title = r["title"]
            pdf_url = r["pdf_url"]
            pub_date = r.get("date", "")

            # Filter by Date (normalize dots to dashes)
            pub_date_normalized = re.sub(r'[\./]', '-', pub_date)
            # If date is not empty and not in target_dates, skip it.
            if pub_date_normalized:
                matched = False
                for td in target_dates:
                    if td in pub_date_normalized:
                        matched = True
                        break
                if not matched:
                    logger.info(f"Skipping report due to date filter ({pub_date}): {title}")
                    continue

            # Check if report already exists in DB
            if db.report_exists(report_key):
                logger.info(f"Report already processed (exists in DB), skipping: {report_key}")
                continue

            logger.info(f"Processing new report: {report_key} - {title}")
            
            # Download PDF
            folder_name = "BOK" if name == "한국은행" else "KDI" if name == "KDI" else "KCIF"
            filename = f"{report_key}.pdf"
            try:
                pdf_path = crawler.download_pdf(pdf_url, folder_name, filename)
                
                # Verify it's actually a PDF
                is_valid_pdf = False
                if os.path.exists(pdf_path):
                    with open(pdf_path, 'rb') as f:
                        header = f.read(4)
                        if header == b'%PDF':
                            is_valid_pdf = True
                            
                if not is_valid_pdf:
                    logger.warning(f"File {pdf_path} is not a valid PDF. Skipping attachment.")
                    os.remove(pdf_path)
                    pdf_path = None
                else:
                    logger.info(f"Downloaded valid PDF to: {pdf_path}")
            except Exception as e:
                logger.error(f"Failed to download PDF for {report_key}: {e}")
                pdf_path = None

            # Summarize PDF using Gemini
            summary_data = None
            if pdf_path:
                try:
                    summary_data = summarizer.summarize_pdf(pdf_path)
                    logger.info(f"Gemini summary generation succeeded for {report_key}")
                except Exception as e:
                    logger.warning(f"Gemini summarization failed for {report_key}: {e}")
            
            if not summary_data:
                summary_data = {
                    "title": title,
                    "summary": ["PDF 원본을 다운로드할 수 없거나 요약에 실패했습니다.", "웹사이트 링크를 통해 직접 확인해주세요."],
                    "implication": {
                        "upside_risk": "-",
                        "downside_risk": "-"
                    },
                    "keywords": ["요약불가"]
                }

            # Map to dashboard format
            dashboard_summary = {
                "title": summary_data.get("title", title),
                "one_line": "",
                "summary_bullets": summary_data.get("summary", []),
                "implication": summary_data.get("implication", {}),
                "keywords": summary_data.get("keywords", []),
                "category": name,
                "date": pub_date_normalized or now.strftime("%Y-%m-%d"),
                "detail_url": "https://www.kcif.or.kr" if name == "국제금융센터" else "https://www.bok.or.kr"
            }

            summaries_for_dashboard.append(dashboard_summary)
            if pdf_path:
                attachment_paths.append(pdf_path)
            
            # Save raw data to add to DB later
            processed_reports.append({
                "key": report_key,
                "name": name,
                "title": title,
                "pdf_path": pdf_path or "",
                "author": r.get("author", ""),
                "date": pub_date_normalized,
                "summary_data": summary_data
            })

    # 6. Send individual emails and update DB
    if not summaries_for_dashboard:
        logger.info("No new reports to send. Exiting.")
        return

    plan_path = os.path.join(os.path.expanduser("~"), ".gemini", "antigravity", "brain", "da71669a-930b-445c-89e6-c43f1da94eae", "implementation_plan.md")
    
    success_count = 0
    for pr, dashboard_summary in zip(processed_reports, summaries_for_dashboard):
        html_body = outlook.generate_news_dashboard_html([dashboard_summary])
        subject = f"[외부기관 보고서 다운로드 파일] {pr['title']}"
        
        attachment_paths = []
        if pr["pdf_path"]:
            attachment_paths.append(pr["pdf_path"])
        if os.path.exists(plan_path):
            attachment_paths.append(plan_path)
            
        draft_success = False
        try:
            draft_success = gmail.send_dashboard(
                subject=subject,
                html_body=html_body,
                attachment_paths=attachment_paths
            )
        except Exception as e:
            logger.error(f"Exception raised while sending Gmail email for {pr['key']}: {e}")

        if draft_success:
            logger.info(f"Successfully sent email for: {pr['title']}")
            success_count += 1
            draft_created_at = datetime.now().isoformat()
            
            try:
                db.add_report(
                    report_key=pr["key"],
                    source_name=pr["name"],
                    title=pr["title"],
                    pdf_path=pr["pdf_path"],
                    author=pr["author"],
                    publish_date=pr["date"],
                    summary_json=json.dumps(pr["summary_data"], ensure_ascii=False),
                    draft_created_at=draft_created_at
                )
                logger.info(f"Successfully registered report in database: {pr['key']}")
            except Exception as e:
                logger.error(f"Failed to save report to database: {pr['key']}. Error: {e}")
        else:
            logger.warning(f"Failed to send email for: {pr['title']}")

    logger.info(f"Financial Reports Monitoring Agent execution finished. (Sent {success_count}/{len(processed_reports)} reports)")

if __name__ == "__main__":
    run_agent()
