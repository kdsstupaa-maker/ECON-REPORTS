import pytest
import os
from src.crawlers.bok_crawler import BOKCrawler

def test_bok_fetch_reports(tmp_path):
    crawler = BOKCrawler(str(tmp_path))
    # 실제 호출 테스트
    reports = crawler.fetch_latest_reports()
    assert isinstance(reports, list)
    assert len(reports) > 0
    
    for report in reports:
        assert "key" in report
        assert report["key"].startswith("bok_")
        assert "title" in report
        assert len(report["title"]) > 0
        assert "pdf_url" in report
        assert report["pdf_url"].startswith("http")
        assert report["pdf_url"].endswith(".pdf")
        assert "author" in report
        assert report["author"] == "한국은행 경제연구원"
        assert "date" in report
        assert len(report["date"]) > 0

def test_bok_download_pdf(tmp_path):
    crawler = BOKCrawler(str(tmp_path))
    reports = crawler.fetch_latest_reports()
    assert len(reports) > 0
    
    report = reports[0]
    # 실제 다운로드 테스트
    pdf_path = crawler.download_pdf(report["pdf_url"], "BOK", f"{report['key']}.pdf")
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0
    assert os.path.abspath(pdf_path) == pdf_path
