import os
import pytest
from src.db_manager import DBManager

def test_db_insert_and_exists(tmp_path):
    db_file = os.path.join(tmp_path, "test.db")
    db = DBManager(db_file)
    db.initialize()
    
    # 1. 존재하지 않는 리포트 조회
    assert db.report_exists("bok_123") is False
    
    # 2. 리포트 추가
    db.add_report(
        report_key="bok_123",
        source_name="한국은행",
        title="테스트 보고서",
        pdf_path="/path/to/pdf"
    )
    
    # 3. 추가 후 조회
    assert db.report_exists("bok_123") is True
