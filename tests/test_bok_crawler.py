import pytest
import os
from unittest.mock import patch, MagicMock
from src.crawlers.bok_crawler import BOKCrawler

MOCK_LIST_HTML = """
<!DOCTYPE html>
<html>
<body>
<div class="bd-line">
    <ul>
        <li>
            <div class="set">
                <a class="title" href="/imer/bbs/P0002456/view.do?nttId=10098447&menuNo=500789">
                    [제2026-11호] Large Zombies, Small Victims: Evidence on Congestion Effects
                </a>
                <div class="btns">
                    <div class="fileGroupSet">
                        <div class="fileGoupBox">
                            <ul>
                                <li>
                                    <a class="i-download" href="/fileSrc/imer/123/1/abc.pdf">1. PDF File.pdf</a>
                                </li>
                                <li>
                                    <a class="i-download" href="/fileSrc/imer/123/2/abc.hwp">2. HWP File.hwp</a>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row dataInfo">
                <span class="date">
                    <span class="hidden">등록일</span>
                    2026.06.15
                </span>
            </div>
        </li>
        <li>
            <div class="set">
                <a class="title" href="/imer/bbs/P0002456/view.do?nttId=10098342&menuNo=500789">
                    [제2026-10호] Green Transition, Energy Substitution
                </a>
                <div class="btns">
                    <div class="fileGroupSet">
                        <div class="fileGoupBox">
                            <ul>
                                <li>
                                    <a class="i-download" href="/fileSrc/imer/456/1/def.pdf">1. PDF File.pdf</a>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row dataInfo">
                <span class="date">
                    <span class="hidden">등록일</span>
                    2026.06.09
                </span>
            </div>
        </li>
        <!-- Item without PDF (should be skipped) -->
        <li>
            <div class="set">
                <a class="title" href="/imer/bbs/P0002456/view.do?nttId=10098000&menuNo=500789">
                    [제2026-9호] No PDF Report
                </a>
            </div>
            <div class="row dataInfo">
                <span class="date">
                    <span class="hidden">등록일</span>
                    2026.06.01
                </span>
            </div>
        </li>
    </ul>
</div>
</body>
</html>
"""

@patch("src.crawlers.bok_crawler.requests.get")
def test_bok_fetch_reports(mock_get, tmp_path):
    # Setup mock response for list page
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = MOCK_LIST_HTML
    mock_resp.apparent_encoding = "utf-8"
    mock_get.return_value = mock_resp
    
    crawler = BOKCrawler(str(tmp_path))
    reports = crawler.fetch_latest_reports()
    
    assert isinstance(reports, list)
    # Check that we fetched exactly 2 reports (skipping the one without PDF)
    assert len(reports) == 2
    
    # Verify the first report details
    r1 = reports[0]
    assert r1["key"] == "bok_10098447"
    assert "Large Zombies, Small Victims" in r1["title"]
    assert r1["pdf_url"] == "https://www.bok.or.kr/fileSrc/imer/123/1/abc.pdf"
    assert r1["author"] == "한국은행 경제연구원"
    # Date should be normalized from 2026.06.15 to 2026-06-15
    assert r1["date"] == "2026-06-15"
    
    # Verify the second report details
    r2 = reports[1]
    assert r2["key"] == "bok_10098342"
    assert "Green Transition, Energy Substitution" in r2["title"]
    assert r2["pdf_url"] == "https://www.bok.or.kr/fileSrc/imer/456/1/def.pdf"
    assert r2["author"] == "한국은행 경제연구원"
    assert r2["date"] == "2026-06-09"

@patch("src.crawlers.base_crawler.requests.get")
def test_bok_download_pdf(mock_get, tmp_path):
    # Setup mock response for stream download
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_content.return_value = [b"chunk1", b"chunk2", b"chunk3"]
    mock_get.return_value = mock_resp
    
    crawler = BOKCrawler(str(tmp_path))
    pdf_url = "https://www.bok.or.kr/fileSrc/imer/123/1/abc.pdf"
    
    pdf_path = crawler.download_pdf(pdf_url, "BOK", "test_report.pdf")
    
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0
    with open(pdf_path, "rb") as f:
        content = f.read()
    assert content == b"chunk1chunk2chunk3"
    
    mock_get.assert_called_once_with(pdf_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, stream=True, timeout=30)
