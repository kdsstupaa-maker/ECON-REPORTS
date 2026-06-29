import pytest
import os
import json
from unittest.mock import MagicMock, patch
from src.services.gemini_service import GeminiSummarizer

@patch("google.generativeai.delete_file")
@patch("google.generativeai.upload_file")
@patch("google.generativeai.GenerativeModel")
def test_gemini_summarize_pdf(mock_model_class, mock_upload, mock_delete, tmp_path):
    # Create a mock PDF file
    pdf_path = os.path.join(tmp_path, "mock.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4 mock content")
        
    # Setup Mock file
    mock_file_obj = MagicMock()
    mock_file_obj.name = "files/mock_file_id"
    mock_file_obj.state.name = "ACTIVE"
    mock_upload.return_value = mock_file_obj
    
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_json_response = {
        "title": "금융 리스크 분석",
        "summary": ["핵심 1", "핵심 2", "핵심 3"],
        "implication": {
            "upside_risk": "금리 하락으로 인한 자산 평가익 증가",
            "downside_risk": "PF 대출 부실화 우려 심화"
        },
        "keywords": ["금리", "신용리스크", "PF"]
    }
    mock_response.text = json.dumps(mock_json_response)
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model
    
    summarizer = GeminiSummarizer(api_key="fake_key", model_name="gemini-1.5-flash")
    result = summarizer.summarize_pdf(pdf_path)
    
    assert result["title"] == "금융 리스크 분석"
    assert len(result["summary"]) == 3
    assert result["implication"]["downside_risk"] == "PF 대출 부실화 우려 심화"
    assert "PF" in result["keywords"]
    
    # Verify mock calls
    mock_upload.assert_called_once_with(path=pdf_path)
    mock_delete.assert_called_once_with("files/mock_file_id")


def test_gemini_summarize_pdf_file_not_found():
    summarizer = GeminiSummarizer(api_key="fake_key", model_name="gemini-1.5-flash")
    with pytest.raises(FileNotFoundError):
        summarizer.summarize_pdf("non_existent_file.pdf")


@patch("google.generativeai.delete_file")
@patch("google.generativeai.get_file")
@patch("google.generativeai.upload_file")
@patch("google.generativeai.GenerativeModel")
@patch("time.sleep")  # Avoid actual sleeping in test
def test_gemini_summarize_pdf_processing_loop(mock_sleep, mock_model_class, mock_upload, mock_get_file, mock_delete, tmp_path):
    pdf_path = os.path.join(tmp_path, "mock.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4 mock content")
        
    # Setup upload_file to return a PROCESSING state file
    mock_file_obj = MagicMock()
    mock_file_obj.name = "files/mock_file_id"
    mock_file_obj.state.name = "PROCESSING"
    mock_upload.return_value = mock_file_obj
    
    # Setup get_file to return PROCESSING first, then ACTIVE
    mock_file_active = MagicMock()
    mock_file_active.name = "files/mock_file_id"
    mock_file_active.state.name = "ACTIVE"
    
    mock_get_file.return_value = mock_file_active
    
    # Model details
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"title": "test", "summary": [], "implication": {"upside_risk": "", "downside_risk": ""}, "keywords": []}'
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model
    
    summarizer = GeminiSummarizer(api_key="fake_key", model_name="gemini-1.5-flash")
    result = summarizer.summarize_pdf(pdf_path)
    
    assert result["title"] == "test"
    mock_get_file.assert_called_once_with("files/mock_file_id")
    mock_sleep.assert_called_once_with(2)
    mock_delete.assert_called_once_with("files/mock_file_id")


@patch("google.generativeai.delete_file")
@patch("google.generativeai.get_file")
@patch("google.generativeai.upload_file")
@patch("google.generativeai.GenerativeModel")
@patch("time.sleep")
def test_gemini_summarize_pdf_failed_state(mock_sleep, mock_model_class, mock_upload, mock_get_file, mock_delete, tmp_path):
    pdf_path = os.path.join(tmp_path, "mock.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4 mock content")
        
    mock_file_obj = MagicMock()
    mock_file_obj.name = "files/mock_file_id"
    mock_file_obj.state.name = "PROCESSING"
    mock_upload.return_value = mock_file_obj
    
    # Setup get_file to return FAILED
    mock_file_failed = MagicMock()
    mock_file_failed.name = "files/mock_file_id"
    mock_file_failed.state.name = "FAILED"
    mock_get_file.return_value = mock_file_failed
    
    summarizer = GeminiSummarizer(api_key="fake_key", model_name="gemini-1.5-flash")
    with pytest.raises(ValueError):
        summarizer.summarize_pdf(pdf_path)
        
    mock_delete.assert_called_once_with("files/mock_file_id")
