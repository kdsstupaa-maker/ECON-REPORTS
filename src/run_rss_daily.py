import sys
import os
import logging
import json
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.db_manager import DBManager
from src.crawlers.rss_crawler import RSSCrawler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("rss_runner")

INSTITUTIONS = [
  {"name": "하나금융연구소", "url": "https://www.hanaif.re.kr"},
  {"name": "현대경제연구원", "url": "https://www.hri.co.kr"},
  {"name": "예금보험공사", "url": "https://www.kdic.or.kr"},
  {"name": "BIS", "url": "https://www.bis.org"},
  {"name": "토지주택연구원", "url": "https://lhi.lh.or.kr"},
  {"name": "국제금융센터", "url": "https://www.kcif.or.kr"},
  {"name": "주택산업연구원", "url": "https://www.khi.re.kr"},
  {"name": "Fed New York", "url": "https://www.newyorkfed.org"},
  {"name": "금감원", "url": "https://www.fss.or.kr"},
  {"name": "무역협회국제무역통상연구원", "url": "https://iit.kita.net"},
  {"name": "건설산업연구원", "url": "https://www.cerik.re.kr"},
  {"name": "부동산연구원", "url": "https://www.reb.or.kr"},
  {"name": "금융연구원", "url": "https://www.kif.re.kr"},
  {"name": "우리금융경영연구소", "url": "https://www.wfri.re.kr"},
  {"name": "fnguide", "url": "https://www.fnguide.com"},
  {"name": "나이스신평", "url": "https://www.nicerating.com"},
  {"name": "대외경제정책연구원", "url": "https://www.kiep.go.kr"},
  {"name": "조세재정연", "url": "https://www.kipf.re.kr"},
  {"name": "산업연구원", "url": "https://www.kiet.re.kr"},
  {"name": "한국경영자협회", "url": "https://www.kefonline.com"},
  {"name": "한신평", "url": "https://www.kisrating.com"},
  {"name": "PIMCO", "url": "https://www.pimco.com/kr"},
  {"name": "OECD", "url": "https://www.oecd.org"},
  {"name": "Fed San Francisco", "url": "https://www.frbsf.org"},
  {"name": "아산정책연구원", "url": "https://www.asaninst.org"},
  {"name": "상공회의소", "url": "https://www.korcham.net"},
  {"name": "자본시장연구원", "url": "https://www.kcmi.re.kr"},
  {"name": "한기평", "url": "https://www.korearatings.com"},
  {"name": "한국리츠협회", "url": "https://www.kareit.or.kr"},
  {"name": "금융위", "url": "https://www.fsc.go.kr"},
  {"name": "포스코경영연구원", "url": "https://www.posri.re.kr"},
  {"name": "한국안보전략연구원", "url": "https://www.inss.re.kr"},
  {"name": "IMF", "url": "https://www.imf.org"},
  {"name": "국회예산정책보고서", "url": "https://www.nabo.go.kr"},
  {"name": "보험연구원", "url": "https://www.kiri.or.kr"},
  {"name": "KDI경제연구원", "url": "https://www.kdi.re.kr"},
  {"name": "국가데이터처", "url": "https://kostat.go.kr"},
  {"name": "BlackRock", "url": "https://www.blackrock.com"},
  {"name": "한국은행", "url": "https://www.bok.or.kr"},
  {"name": "kb금융연구소", "url": "https://www.kbfg.com/kbresearch"}
]

def run():
    logger.info("Starting RSS Crawling for 40+ institutions (Last 3 days)...")
    db_path = os.path.join(project_root, "data", "bok_news.db")
    db = DBManager(db_path)
    db.initialize()
    
    crawler = RSSCrawler(target_days=3)
    reports = crawler.fetch_feeds(INSTITUTIONS)
    
    success_count = 0
    for r in reports:
        if not db.report_exists(r["key"]):
            try:
                db.add_report(
                    report_key=r["key"],
                    source_name=r["name"],
                    title=r["title"],
                    pdf_path=r["pdf_url"], # Treat link as pdf_path so UI can open link
                    author=r["author"],
                    publish_date=r["date"],
                    summary_json=json.dumps(r["summary_data"], ensure_ascii=False),
                    draft_created_at=datetime.now().isoformat()
                )
                success_count += 1
                logger.info(f"Added {r['name']} report: {r['title']}")
            except Exception as e:
                logger.error(f"Error saving {r['title']}: {e}")
                
    logger.info(f"Finished RSS Crawling. Added {success_count} new reports.")

if __name__ == "__main__":
    run()
