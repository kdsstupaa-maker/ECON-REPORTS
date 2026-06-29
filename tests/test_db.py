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
        pdf_path="/path/to/pdf",
        draft_created_at="2026-06-29T12:00:00"
    )
    
    # 3. 추가 후 조회
    assert db.report_exists("bok_123") is True

    # 4. 필드 저장 여부 검증
    import sqlite3
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT report_key, source_name, title, pdf_path, draft_created_at FROM reports WHERE report_key = ?", ("bok_123",))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "bok_123"
        assert row[1] == "한국은행"
        assert row[2] == "테스트 보고서"
        assert row[3] == "/path/to/pdf"
        assert row[4] == "2026-06-29T12:00:00"

def test_db_duplicate_insert(tmp_path):
    db_file = os.path.join(tmp_path, "test.db")
    db = DBManager(db_file)
    db.initialize()
    
    db.add_report("bok_123", "source1", "title1", "path1")
    
    # This should not raise sqlite3.IntegrityError
    db.add_report("bok_123", "source2", "title2", "path2")
    
    # Verify that the first insert is kept (using INSERT OR IGNORE)
    import sqlite3
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT source_name, title, pdf_path FROM reports WHERE report_key = ?", ("bok_123",))
        row = cursor.fetchone()
        assert row[0] == "source1"


