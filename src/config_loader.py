"""
설정 파일 로더 (config/config.yaml + 환경변수)
"""

import yaml
import os


class Config:
    def __init__(self, config_path="config/config.yaml"):
        if not os.path.exists(config_path):
            raise RuntimeError(f"Config file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.data = yaml.safe_load(f) or {}
        except Exception as e:
            raise RuntimeError(f"Error loading config file {config_path}: {e}")

        gemini = self.data.get("gemini") or {}
        email = self.data.get("email") or {}
        storage = self.data.get("storage") or {}
        crawling = self.data.get("crawling") or {}

        # Gemini
        self.gemini_key = os.getenv("GEMINI_API_KEY") or gemini.get("api_key", "")
        self.gemini_model = gemini.get("model", "gemini-1.5-flash")

        # Email
        self.email_recipient = email.get("recipient", "")
        self.email_subject_prefix = email.get("subject_prefix", "[BOK 일일 브리핑]")
        self.email_send_mode = email.get("send_mode", "draft")  # "send" | "draft"
        # Gmail
        self.gmail_sender = os.getenv("GMAIL_SENDER") or email.get("gmail_sender", "")
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD") or email.get("gmail_app_password", "")

        # Storage
        self.db_path = storage.get("db_path", "data/bok_news.db")
        self.pdf_dir = storage.get("pdf_dir", "data/pdfs")

        # KCIF
        kcif = self.data.get("kcif") or {}
        self.kcif_id = kcif.get("id", "")
        self.kcif_pwd = kcif.get("pwd", "")

        # Crawling
        self.crawling_url = crawling.get(
            "target_url",
            "https://www.bok.or.kr/portal/singl/newsData/list.do?menuNo=201150&sort=1&pageUnit=10"
        )
        self.crawling_today_only = crawling.get("today_only", True)
        self.crawling_max_items = crawling.get("max_items", 10)
        self.crawling_download_attachments = crawling.get("download_attachments", True)

        # 필수 항목 검증
        missing = []
        if not self.gemini_key:
            missing.append("gemini.api_key (또는 환경변수 GEMINI_API_KEY)")
        if not self.email_recipient:
            missing.append("email.recipient")

        if missing:
            raise RuntimeError(f"필수 설정 누락: {', '.join(missing)}")
