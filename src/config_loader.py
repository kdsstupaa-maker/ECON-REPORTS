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
            
        gemini = self.data.get("gemini")
        if not isinstance(gemini, dict):
            gemini = {}
        email = self.data.get("email")
        if not isinstance(email, dict):
            email = {}
        storage = self.data.get("storage")
        if not isinstance(storage, dict):
            storage = {}

        self.gemini_key = os.getenv("GEMINI_API_KEY") or gemini.get("api_key")
        self.gemini_model = gemini.get("model")
        self.email_recipient = email.get("recipient")
        self.db_path = storage.get("db_path")
        self.pdf_dir = storage.get("pdf_dir")

        missing = []
        if not self.gemini_key:
            missing.append("gemini.api_key")
        if not self.gemini_model:
            missing.append("gemini.model")
        if not self.email_recipient:
            missing.append("email.recipient")
        if not self.db_path:
            missing.append("storage.db_path")
        if not self.pdf_dir:
            missing.append("storage.pdf_dir")

        if missing:
            raise RuntimeError(f"Missing required config key(s): {', '.join(missing)}")

