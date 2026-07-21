"""
BOK 일일 뉴스/자료 브리핑 — 메인 실행 스크립트
=================================================
사용법:
  python run_bok_daily.py

동작 흐름:
  1. config/config.yaml + 환경변수에서 설정 로드
  2. BOKNewsCrawler로 한국은행 뉴스/자료 섹션 크롤링
  3. 각 자료의 PDF 첨부파일 다운로드
  4. Gemini AI로 자산운용·여신 관점 요약 생성
  5. SQLite DB에 처리 이력 저장 (중복 방지)
  6. 통합 HTML 대시보드 이메일 생성 후 발송
"""

import sys
import os
import json
import logging
from datetime import datetime, date

# 프로젝트 루트를 sys.path에 추가 (어떤 디렉터리에서 실행해도 동작)
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config_loader import Config
from src.db_manager import DBManager
from src.crawlers.bok_news_crawler import BOKNewsCrawler
from src.services.gemini_service import GeminiSummarizer
from src.services.gmail_service import GmailService
from src.services.outlook_service import OutlookService  # HTML 생성용으로 유지

# ─── 로깅 설정 ────────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
log_filename = os.path.join("logs", f"bok_daily_{date.today().strftime('%Y%m%d')}.log")

# Windows CP949 콘솔 인코딩 문제 방지: stdout을 UTF-8로 강제 설정
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_filename, encoding="utf-8"),
    ],
)
logger = logging.getLogger("bok_daily")


# ─── 메인 실행 함수 ───────────────────────────────────────────────────────────

def run():
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("  BOK Daily Intelligence 시작")
    logger.info(f"  실행 시각: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # ── 1. 설정 로드 ──────────────────────────────────────────────────────────
    try:
        config = Config()
        logger.info(f"[OK] 설정 로드 완료 (수신자: {config.email_recipient}, "
                    f"발송 모드: {config.email_send_mode})")
    except RuntimeError as e:
        logger.error(f"[ERROR] 설정 로드 실패: {e}")
        logger.error("   config/config.yaml을 확인하거나 GEMINI_API_KEY 환경변수를 설정하세요.")
        sys.exit(1)

    # ── 2. DB 초기화 ──────────────────────────────────────────────────────────
    try:
        db = DBManager(config.db_path)
        db.initialize()
        logger.info(f"[OK] DB 초기화 완료: {config.db_path}")
    except Exception as e:
        logger.error(f"[ERROR] DB 초기화 실패: {e}")
        sys.exit(1)

    # ── 3. 서비스 초기화 ──────────────────────────────────────────────────────
    try:
        summarizer = GeminiSummarizer(
            api_key=config.gemini_key,
            model_name=config.gemini_model,
        )
        # Gmail 서비스 초기화
        if not config.gmail_sender or not config.gmail_app_password:
            logger.error("[ERROR] Gmail 설정 누락: config.yaml의 gmail_sender, gmail_app_password를 입력하세요.")
            sys.exit(1)
        gmail = GmailService(
            sender_email=config.gmail_sender,
            app_password=config.gmail_app_password,
            recipient=config.email_recipient,
        )
        # HTML 대시보드 생성용 OutlookService (발송에는 사용 안 함)
        outlook = OutlookService(
            recipient=config.email_recipient,
            send_mode="draft",
        )
        logger.info(f"[OK] Gemini 모델: {config.gemini_model}")
        logger.info(f"[OK] Gmail 발신자: {config.gmail_sender}")
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"[ERROR] 서비스 초기화 실패: {e}")
        sys.exit(1)

    # ── 4. 크롤링 ─────────────────────────────────────────────────────────────
    pdf_base_dir = os.path.join(config.pdf_dir, "BOK_NEWS")
    crawler = BOKNewsCrawler(
        pdf_dir=config.pdf_dir,
        today_only=config.crawling_today_only,
        max_items=config.crawling_max_items,
    )

    try:
        news_items = crawler.fetch_today_news()
        logger.info(f"[OK] 크롤링 완료: {len(news_items)}건")
    except Exception as e:
        logger.error(f"[ERROR] 크롤링 실패: {e}")
        sys.exit(1)

    if not news_items:
        logger.warning("[WARN] 수집된 자료가 없습니다. 오늘 신규 게시물이 없거나 사이트 구조가 변경되었을 수 있습니다.")
        logger.info("  처리를 종료합니다.")
        return

    # ── 5. 각 자료 처리 (다운로드 → 요약 → DB 저장) ─────────────────────────
    processed_summaries = []  # 이메일 대시보드에 포함할 요약 목록

    for item in news_items:
        key = item["key"]
        title = item["title"]

        logger.info(f"\n{'─'*50}")
        logger.info(f"  처리 중: {title[:50]}")

        # 중복 체크
        if db.report_exists(key):
            logger.info(f"  [SKIP] 이미 처리된 자료 (건너뜀): {key}")
            continue

        # PDF 다운로드
        file_paths = []
        if config.crawling_download_attachments and item.get("attachments"):
            logger.info(f"[DOWN] 첨부파일 다운로드 중... ({len(item['attachments'])}개 발견)")
            file_paths = crawler.download_attachments(item)
            logger.info(f"[FILE] 다운로드 완료: {len(file_paths)}개")
        else:
            logger.info("  [INFO] 첨부파일 없음 또는 다운로드 비활성화")

        # Gemini 요약
        summary_data = None
        pdf_paths = [p for p in file_paths if p.lower().endswith(".pdf")]

        if pdf_paths:
            try:
                logger.info(f"[AI] Gemini 요약 시작: {os.path.basename(pdf_paths[0])}")
                summary_data = summarizer.summarize_news_pdf(pdf_paths[0], title=title)
                logger.info(f"[OK] 요약 완료: {summary_data.get('one_line', '')[:50]}")
            except Exception as e:
                logger.warning(f"[WARN] Gemini 요약 실패: {e}")
                summary_data = summarizer._build_fallback(title)
        else:
            logger.warning("  [WARN] PDF 없음 — 제목 기반 텍스트 요약 시도")
            try:
                summary_data = summarizer.summarize_text(title, title=title)
            except Exception as e:
                logger.warning(f"[WARN] 텍스트 요약도 실패: {e}")
                summary_data = summarizer._build_fallback(title)

        # 이메일 대시보드 데이터에 메타 정보 병합
        summary_data["category"] = item.get("category", "한국은행 뉴스/자료")
        summary_data["date"] = item.get("date", "")
        summary_data["detail_url"] = item.get("detail_url", "https://www.bok.or.kr")
        summary_data["file_paths"] = file_paths
        processed_summaries.append(summary_data)

        # DB 저장
        try:
            db.add_report(
                report_key=key,
                source_name="한국은행 뉴스/자료",
                title=title,
                pdf_path=str(file_paths[0]) if file_paths else "",
                author="한국은행",
                publish_date=item.get("date", ""),
                summary_json=json.dumps(summary_data, ensure_ascii=False),
                draft_created_at=datetime.now().isoformat(),
            )
            logger.info(f"[DB] DB 저장 완료: {key}")
        except Exception as e:
            logger.error(f"  [ERROR] DB 저장 실패: {e}")

    # ── 6. 이메일 대시보드 생성 및 발송 ──────────────────────────────────────
    logger.info(f"\n{'='*60}")
    logger.info(f"  이메일 생성 중 ({len(processed_summaries)}건 요약 포함)")

    if not processed_summaries:
        logger.warning("[WARN] 이메일 발송 대상이 없습니다. (모두 이미 처리됨 또는 오류)")
        logger.info(f"  총 소요 시간: {(datetime.now() - start_time).seconds}초")
        return

    try:
        today_str = date.today().strftime("%Y년 %m월 %d일")
        subject = (
            f"{config.email_subject_prefix} {today_str} "
            f"— 금일 {len(processed_summaries)}건"
        )
        html_body = outlook.generate_news_dashboard_html(
            summaries=processed_summaries,
            report_date=today_str,
        )

        # 모든 PDF 첨부
        all_attachments = []
        for s in processed_summaries:
            all_attachments.extend(s.get("file_paths", []))
        # 존재하는 파일만 필터링
        all_attachments = [p for p in all_attachments if os.path.exists(p)]

        logger.info(f"  [MAIL] Gmail 발송 중...")
        logger.info(f"     제목: {subject}")
        logger.info(f"     첨부: {len(all_attachments)}개 파일")

        success = gmail.send_dashboard(
            subject=subject,
            html_body=html_body,
            attachment_paths=all_attachments,
        )

        if success:
            logger.info(f"[OK] Gmail 발송 완료 -> {config.email_recipient}")
        else:
            logger.error("  [ERROR] Gmail 발송 실패 — 로그를 확인하세요.")

    except Exception as e:
        logger.error(f"[ERROR] 이메일 생성/발송 중 오류: {e}", exc_info=True)

    # ── 완료 ──────────────────────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).seconds
    logger.info(f"\n{'='*60}")
    logger.info(f"  BOK Daily Intelligence 완료")
    logger.info(f"  처리: {len(processed_summaries)}건 | 소요: {elapsed}초")
    logger.info(f"  로그: {log_filename}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
