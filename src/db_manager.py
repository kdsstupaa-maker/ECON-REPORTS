import sqlite3
import os

class DBManager:
    def __init__(self, db_path):
        self.db_path = db_path
        if os.path.dirname(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def initialize(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_key TEXT UNIQUE,
                    source_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT,
                    publish_date TEXT,
                    pdf_path TEXT NOT NULL,
                    summary_json TEXT,
                    draft_created_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def report_exists(self, report_key):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM reports WHERE report_key = ?", (report_key,))
            return cursor.fetchone() is not None

    def add_report(self, report_key, source_name, title, pdf_path, author=None, publish_date=None, summary_json=None, draft_created_at=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reports (report_key, source_name, title, pdf_path, author, publish_date, summary_json, draft_created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (report_key, source_name, title, pdf_path, author, publish_date, summary_json, draft_created_at))
            conn.commit()

