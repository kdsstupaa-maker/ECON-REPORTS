import pytest
import os
import sys
from unittest.mock import MagicMock, patch, mock_open
from src.services.outlook_service import OutlookService

def test_create_draft_windows(tmp_path):
    # Mock the Outlook application
    mock_dispatch = MagicMock()
    mock_outlook = MagicMock()
    mock_mail = MagicMock()
    mock_outlook.CreateItem.return_value = mock_mail
    mock_dispatch.return_value = mock_outlook
    
    # Create a real temp file for the attachment
    temp_file = tmp_path / "test.pdf"
    temp_file.write_bytes(b"dummy pdf content")
    
    # Force platform flag to be win32
    with patch("sys.platform", "win32"):
        # Mock win32com in sys.modules to prevent real import side-effects on other platforms
        mock_win32com = MagicMock()
        mock_win32com.client = MagicMock()
        mock_win32com.client.Dispatch = mock_dispatch
        
        with patch.dict("sys.modules", {"win32com": mock_win32com, "win32com.client": mock_win32com.client}):
            service = OutlookService(recipient="test@example.com")
            success = service.create_draft(
                subject="[테스트] 요약본",
                body="<h1>이메일 테스트</h1>",
                attachment_paths=[str(temp_file)]
            )
            
            assert success is True
            mock_dispatch.assert_called_once_with("Outlook.Application")
            mock_outlook.CreateItem.assert_called_once_with(0)
            assert mock_mail.To == "test@example.com"
            assert mock_mail.Subject == "[테스트] 요약본"
            assert mock_mail.HTMLBody == "<h1>이메일 테스트</h1>"
            mock_mail.Attachments.Add.assert_called_once_with(os.path.abspath(str(temp_file)))
            mock_mail.Save.assert_called_once()

@patch("src.services.outlook_service.os.makedirs")
@patch("src.services.outlook_service.open", new_callable=mock_open)
def test_create_draft_non_windows(mock_file, mock_makedirs):
    # Force platform flag to be non-win32 (e.g. linux)
    with patch("sys.platform", "linux"):
        service = OutlookService(recipient="test@example.com")
        success = service.create_draft(
            subject="[테스트] 요약본",
            body="<h1>이메일 테스트</h1>",
            attachment_paths=["/path/to/test.pdf"]
        )
        
        assert success is True
        # Verify it tries to create 'data/drafts' folder
        mock_makedirs.assert_called_once_with("data/drafts", exist_ok=True)
        # Verify it writes to some HTML file inside data/drafts/
        mock_file.assert_called_once()
        
        # Check that it writes the body containing attachment waiting info
        written_content = mock_file().write.call_args[0][0]
        assert "이메일 테스트" in written_content
        assert "[첨부파일 대기]" in written_content
        assert "test.pdf" in written_content


def test_generate_html_body():
    service = OutlookService(recipient="test@example.com")
    html = service.generate_html_body(
        source="한국은행",
        title="통화신용정책보고서 분석",
        summary=["금리 인상 영향 지속", "가계대출 증가세 둔화"],
        implication={
            "upside_risk": "인플레이션 압력 완화 가능성",
            "downside_risk": "경기 침체 동반 가능성 우려"
        },
        keywords=["금리", "가계대출", "통화정책"],
        pdf_name="bok_report_2026.pdf"
    )
    
    assert "통화신용정책보고서 분석" in html
    assert "한국은행" in html
    assert "금리 인상 영향 지속" in html
    assert "인플레이션 압력 완화 가능성" in html
    assert "경기 침체 동반 가능성 우려" in html
    assert "bok_report_2026.pdf" in html
    assert "금리" in html
    assert "가계대출" in html
    assert "통화정책" in html
    assert "<html>" in html.lower()

def test_create_draft_windows_exception():
    # Mock the win32com client dispatch to raise Exception
    mock_dispatch = MagicMock(side_effect=Exception("COM initialization failed"))
    
    # Force platform flag to be win32
    with patch("sys.platform", "win32"):
        mock_win32com = MagicMock()
        mock_win32com.client = MagicMock()
        mock_win32com.client.Dispatch = mock_dispatch
        
        with patch.dict("sys.modules", {"win32com": mock_win32com, "win32com.client": mock_win32com.client}):
            service = OutlookService(recipient="test@example.com")
            success = service.create_draft(
                subject="[테스트] 오류 테스트",
                body="<h1>오류 테스트</h1>"
            )
            assert success is False

def test_create_draft_windows_missing_attachment(tmp_path):
    mock_dispatch = MagicMock()
    mock_outlook = MagicMock()
    mock_mail = MagicMock()
    mock_outlook.CreateItem.return_value = mock_mail
    mock_dispatch.return_value = mock_outlook
    
    # Create one existing attachment and one missing attachment
    existing_file = tmp_path / "exist.pdf"
    existing_file.write_bytes(b"dummy pdf content")
    missing_file = tmp_path / "missing.pdf"
    
    # Force platform flag to be win32
    with patch("sys.platform", "win32"):
        mock_win32com = MagicMock()
        mock_win32com.client = MagicMock()
        mock_win32com.client.Dispatch = mock_dispatch
        
        with patch.dict("sys.modules", {"win32com": mock_win32com, "win32com.client": mock_win32com.client}):
            service = OutlookService(recipient="test@example.com")
            success = service.create_draft(
                subject="[테스트] 미존재 첨부파일",
                body="<h1>미존재 첨부파일</h1>",
                attachment_paths=[str(existing_file), str(missing_file)]
            )
            
            assert success is True
            # Assert only the existing file is added to attachments
            mock_mail.Attachments.Add.assert_called_once_with(os.path.abspath(str(existing_file)))
            mock_mail.Save.assert_called_once()


