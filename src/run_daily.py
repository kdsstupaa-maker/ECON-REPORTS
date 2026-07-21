import sys
import os
import logging
import json
from datetime import datetime, timedelta

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.db_manager import DBManager
from src.crawlers.bok_crawler import BOKCrawler
from src.crawlers.bok_news_crawler import BOKNewsCrawler
from src.crawlers.kdi_crawler import KDICrawler
from src.crawlers.kcif_crawler import KCIFCrawler
from src.crawlers.kiet_crawler import KIETCrawler
from src.crawlers.fss_crawler import FSSCrawler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("run_daily")

def run():
    logger.info("Starting Daily Crawling for 5 Key Institutions...")
    db_path = os.path.join(project_root, "data", "bok_news.db")
    db = DBManager(db_path)
    db.initialize()
    
    # 30 days ago limit to include KDI and KIET's recent but not-so-recent data
    cutoff_date = datetime.now() - timedelta(days=30)
    cutoff_date_str = cutoff_date.strftime("%Y-%m-%d")
    
    pdf_dir = os.path.join(project_root, "data", "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    
    crawlers = [
        ("한국은행 (Research)", BOKCrawler(pdf_dir)),
        ("한국은행 (News)", BOKNewsCrawler(pdf_dir)),
        ("KDI경제연구원", KDICrawler(pdf_dir)),
        ("국제금융센터", KCIFCrawler(pdf_dir, "dummy_id", "dummy_pwd")),
        ("산업연구원", KIETCrawler(pdf_dir)),
        ("금감원", FSSCrawler(pdf_dir)),
    ]
    
    total_added = 0
    for name, crawler in crawlers:
        logger.info(f"Crawling {name}...")
        try:
            reports = crawler.fetch_latest_reports()
            logger.info(f"Fetched {len(reports)} total items from {name}")
            
            added_count = 0
            for r in reports:
                # Filter older than 3 days
                report_date = r.get("date", "")
                if report_date and report_date < cutoff_date_str:
                    continue
                    
                if not db.report_exists(r["key"]):
                    db.add_report(
                        report_key=r["key"],
                        source_name=r.get("author", name),
                        title=r["title"],
                        pdf_path=r["pdf_url"], 
                        author=r.get("author", ""),
                        publish_date=report_date,
                        summary_json=json.dumps({
                            "title": r["title"],
                            "summary": ["본문 수집 중"] if "kiet" in r["key"] or "fss" in r["key"] else ["수집 완료"],
                            "implication": {"upside_risk": "-", "downside_risk": "-"},
                            "keywords": ["핵심기관"]
                        }, ensure_ascii=False),
                        draft_created_at=datetime.now().isoformat()
                    )
                    added_count += 1
                    logger.info(f"Added new report: {r['title']} from {name}")
            total_added += added_count
            logger.info(f"Finished {name}. Added {added_count} new reports within 3 days.")
        except Exception as e:
            logger.error(f"Error crawling {name}: {e}")
            
    logger.info(f"Finished all crawling. Added {total_added} total reports.")

if __name__ == "__main__":
    run()
