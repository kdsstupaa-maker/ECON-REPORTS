import pytest
import os
import datetime
from unittest.mock import MagicMock, patch
from src.crawlers.kdi_crawler import KDICrawler

@patch("requests.get")
def test_kdi_fetch_reports(mock_get):
    # Mock the list page response
    mock_list_resp = MagicMock()
    mock_list_resp.status_code = 200
    mock_list_resp.content = '''
    <div class="page_list-group">
        <ul>
            <li>
                <a href="./focusView?pub_no=19187">
                    <div class="rpt_tit">
                        <b class="fcs">KDI FOCUS</b>
                        <strong>의무휴업 및 영업제한...</strong>
                    </div>
                </a>
                <div class="rpt_other">
                    <p>
                        <span>이진국</span>
                        <span>12p</span>
                    </p>
                </div>
                <div class="rpt_link">
                    <button class="i02" onclick='location.href="/file/download?atch_no=abc"' type="button">PDF 다운로드</button>
                </div>
            </li>
        </ul>
    </div>
    '''.encode('utf-8')
    
    # Mock the detail page response
    mock_detail_resp = MagicMock()
    mock_detail_resp.status_code = 200
    mock_detail_resp.content = '''
    <div class="top_bg-wrap">
        <strong class="title">
            <b>KDI FOCUS</b>
            <p>의무휴업 및 영업제한...</p>
            <span>2026.05.21.</span>
        </strong>
    </div>
    '''.encode('utf-8')
    
    mock_get.side_effect = [mock_list_resp, mock_detail_resp]
    
    crawler = KDICrawler("/tmp/pdf")
    reports = crawler.fetch_latest_reports()
    
    assert len(reports) == 1
    report = reports[0]
    assert report["key"] == "kdi_19187"
    assert report["title"] == "의무휴업 및 영업제한..."
    assert report["pdf_url"] == "https://www.kdi.re.kr/file/download?atch_no=abc"
    assert report["author"] == "이진국"
    assert report["date"] == "2026-05-21"


@patch("requests.get")
def test_kdi_fetch_reports_fallback_date(mock_get):
    # Mock the list page response
    mock_list_resp = MagicMock()
    mock_list_resp.status_code = 200
    mock_list_resp.content = '''
    <div class="page_list-group">
        <ul>
            <li>
                <a href="./focusView?pub_no=19187">
                    <div class="rpt_tit">
                        <b class="fcs">KDI FOCUS</b>
                        <strong>의무휴업 및 영업제한...</strong>
                    </div>
                </a>
                <div class="rpt_other">
                    <p>
                        <span>이진국</span>
                        <span>12p</span>
                    </p>
                </div>
                <div class="rpt_link">
                    <button class="i02" onclick="location.href=\'/file/download?atch_no=abc\'" type="button">PDF 다운로드</button>
                </div>
            </li>
        </ul>
    </div>
    '''.encode('utf-8')
    
    # Mock the detail page response raising exception
    mock_get.side_effect = [mock_list_resp, Exception("Network error")]
    
    crawler = KDICrawler("/tmp/pdf")
    reports = crawler.fetch_latest_reports()
    
    assert len(reports) == 1
    report = reports[0]
    assert report["key"] == "kdi_19187"
    assert report["date"] == datetime.date.today().isoformat()


@patch("requests.get")
def test_kdi_fetch_reports_empty_list(mock_get):
    mock_list_resp = MagicMock()
    mock_list_resp.status_code = 200
    mock_list_resp.content = '<div>No reports</div>'.encode('utf-8')
    
    mock_get.return_value = mock_list_resp
    
    crawler = KDICrawler("/tmp/pdf")
    reports = crawler.fetch_latest_reports()
    
    assert len(reports) == 0


@patch("requests.get")
def test_kdi_fetch_reports_limits_to_five(mock_get):
    # Mock list page with 7 items
    mock_list_resp = MagicMock()
    mock_list_resp.status_code = 200
    
    li_template = '''
            <li>
                <a href="./focusView?pub_no={pub_no}">
                    <div class="rpt_tit">
                        <b class="fcs">KDI FOCUS</b>
                        <strong>의무휴업 및 영업제한...</strong>
                    </div>
                </a>
                <div class="rpt_other">
                    <p>
                        <span>이진국</span>
                        <span>12p</span>
                    </p>
                </div>
                <div class="rpt_link">
                    <button class="i02" onclick="location.href='/file/download?atch_no=abc'" type="button">PDF 다운로드</button>
                </div>
            </li>
    '''
    
    lis = "".join(li_template.format(pub_no=10000 + i) for i in range(7))
    mock_list_resp.content = f'''
    <div class="page_list-group">
        <ul>
            {lis}
        </ul>
    </div>
    '''.encode('utf-8')
    
    # Mock detail page response
    mock_detail_resp = MagicMock()
    mock_detail_resp.status_code = 200
    mock_detail_resp.content = '''
    <div class="top_bg-wrap">
        <strong class="title">
            <b>KDI FOCUS</b>
            <p>의무휴업 및 영업제한...</p>
            <span>2026.05.21</span>
        </strong>
    </div>
    '''.encode('utf-8')
    
    # Return list page first, then detail pages
    mock_get.side_effect = [mock_list_resp] + [mock_detail_resp] * 10
    
    crawler = KDICrawler("/tmp/pdf")
    reports = crawler.fetch_latest_reports()
    
    assert len(reports) == 5
    # Total calls: 1 for list page, 5 for detail pages = 6 calls
    assert mock_get.call_count == 6

