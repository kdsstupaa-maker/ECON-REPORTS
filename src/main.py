import sys
import os
import logging
import json
from datetime import datetime

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main_runner")

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
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        return

    # 4. Initialize Crawlers
    crawlers = [
        ("한국은행", BOKCrawler(config.pdf_dir)),
        ("KDI", KDICrawler(config.pdf_dir))
    ]

    # 5. Process Crawled Reports
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
            
            # Check if report already exists in DB
            if db.report_exists(report_key):
                logger.info(f"Report already processed (exists in DB), skipping: {report_key}")
                continue

            logger.info(f"Processing new report: {report_key} - {title}")
            
            # Download PDF
            folder_name = "BOK" if name == "한국은행" else "KDI"
            filename = f"{report_key}.pdf"
            try:
                pdf_path = crawler.download_pdf(pdf_url, folder_name, filename)
                logger.info(f"Downloaded PDF to: {pdf_path}")
            except Exception as e:
                logger.error(f"Failed to download PDF for {report_key}: {e}")
                continue

            # Summarize PDF using Gemini
            try:
                summary_data = summarizer.summarize_pdf(pdf_path)
                logger.info(f"Gemini summary generation succeeded for {report_key}")
            except Exception as e:
                logger.warning(f"Gemini summarization failed for {report_key}, falling back to dummy data. Error: {e}")
                summary_data = {
                    "title": title,
                    "summary": ["PDF 요약 분석에 실패했습니다. (요약 생성 실패)"],
                    "implication": {
                        "upside_risk": "분석 실패로 기회 요인을 도출할 수 없습니다.",
                        "downside_risk": "분석 실패로 위험 요인을 도출할 수 없습니다."
                    },
                    "keywords": ["오류", "분석실패"]
                }

            # Generate HTML body and Create Outlook draft
            pdf_basename = os.path.basename(pdf_path)
            html_body = outlook.generate_html_body(
                source=name,
                title=summary_data.get("title", title),
                summary=summary_data.get("summary", []),
                implication=summary_data.get("implication", {}),
                keywords=summary_data.get("keywords", []),
                pdf_name=pdf_basename
            )

            subject = f"[{name}] {summary_data.get('title', title)}"
            
            draft_success = False
            try:
                draft_success = outlook.create_draft(
                    subject=subject,
                    body=html_body,
                    attachment_paths=[pdf_path]
                )
            except Exception as e:
                logger.error(f"Exception raised while creating Outlook draft for {report_key}: {e}")

            if draft_success:
                logger.info(f"Successfully created Outlook draft for {report_key}")
                draft_created_at = datetime.now().isoformat()
            else:
                logger.warning(f"Failed to create Outlook draft for {report_key}")
                draft_created_at = None

            # Register in Database
            try:
                db.add_report(
                    report_key=report_key,
                    source_name=name,
                    title=title,
                    pdf_path=pdf_path,
                    author=r.get("author"),
                    publish_date=r.get("date"),
                    summary_json=json.dumps(summary_data, ensure_ascii=False),
                    draft_created_at=draft_created_at
                )
                logger.info(f"Successfully registered report in database: {report_key}")
            except Exception as e:
                logger.error(f"Failed to save report to database: {report_key}. Error: {e}")

    logger.info("Financial Reports Monitoring Agent execution finished.")

if __name__ == "__main__":
    run_agent()
