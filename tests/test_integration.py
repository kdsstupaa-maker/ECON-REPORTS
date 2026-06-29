import pytest
from unittest.mock import MagicMock, patch
from src.main import run_agent

@patch("src.main.Config")
@patch("src.main.DBManager")
@patch("src.main.BOKCrawler")
@patch("src.main.KDICrawler")
@patch("src.main.GeminiSummarizer")
@patch("src.main.OutlookService")
def test_run_agent_integration(mock_outlook, mock_gemini, mock_kdi, mock_bok, mock_db, mock_config):
    # Setup config mocks
    mock_config_inst = MagicMock()
    mock_config_inst.gemini_key = "fake_key"
    mock_config_inst.gemini_model = "fake_model"
    mock_config_inst.email_recipient = "test@test.com"
    mock_config_inst.db_path = ":memory:"
    mock_config_inst.pdf_dir = "mock_pdfs"
    mock_config.return_value = mock_config_inst

    # Setup DB Mock
    mock_db_inst = MagicMock()
    mock_db_inst.report_exists.return_value = False
    mock_db.return_value = mock_db_inst

    # Setup BOK Crawler Mock
    mock_bok_inst = MagicMock()
    mock_bok_inst.fetch_latest_reports.return_value = [{
        "key": "bok_100", "title": "BOK 리포트", "pdf_url": "http://bok.com/100.pdf", "author": "BOK", "date": "2026-06-29"
    }]
    mock_bok_inst.download_pdf.return_value = "mock_pdfs/bok_100.pdf"
    mock_bok.return_value = mock_bok_inst

    # Setup KDI Crawler Mock
    mock_kdi_inst = MagicMock()
    mock_kdi_inst.fetch_latest_reports.return_value = []
    mock_kdi.return_value = mock_kdi_inst

    # Setup Gemini Mock
    mock_gemini_inst = MagicMock()
    mock_gemini_inst.summarize_pdf.return_value = {
        "title": "BOK 리포트",
        "summary": ["요약1", "요약2", "요약3"],
        "implication": {"upside_risk": "상승", "downside_risk": "하락"},
        "keywords": ["키워드"]
    }
    mock_gemini.return_value = mock_gemini_inst

    # Run Agent Orchestrator
    run_agent()

    # Assertions
    mock_bok_inst.fetch_latest_reports.assert_called_once()
    mock_gemini_inst.summarize_pdf.assert_called_with("mock_pdfs/bok_100.pdf")
    mock_db_inst.add_report.assert_called_once()
    mock_outlook.return_value.create_draft.assert_called_once()
