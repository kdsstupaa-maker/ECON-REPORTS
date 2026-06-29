import pytest
import os
from src.crawlers.bok_crawler import BOKCrawler

def test_bok_fetch_reports(tmp_path):
    crawler = BOKCrawler(str(tmp_path))
    # 실제 호출 테스트
    reports = crawler.fetch_latest_reports()
    assert isinstance(reports, list)
    if len(reports) > 0:
        report = reports[0]
        assert "key" in report
        assert "title" in report
        assert "pdf_url" in report
        assert report["pdf_url"].startswith("http")
