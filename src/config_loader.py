import yaml
import os

class Config:
    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)
        
        self.gemini_key = self.data["gemini"]["api_key"]
        self.gemini_model = self.data["gemini"]["model"]
        self.email_recipient = self.data["email"]["recipient"]
        self.db_path = self.data["storage"]["db_path"]
        self.pdf_dir = self.data["storage"]["pdf_dir"]
