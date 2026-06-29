import os
import pytest
from src.config_loader import Config

def test_config_load(tmp_path):
    config_file = os.path.join(tmp_path, "config.yaml")
    with open(config_file, "w", encoding="utf-8") as f:
        f.write("""
gemini:
  api_key: "TEST_API_KEY"
  model: "gemini-1.5-flash"
email:
  recipient: "test@example.com"
storage:
  db_path: "test_db.db"
  pdf_dir: "test_pdfs"
""")
    
    cfg = Config(config_file)
    assert cfg.gemini_key == "TEST_API_KEY"
    assert cfg.gemini_model == "gemini-1.5-flash"
    assert cfg.email_recipient == "test@example.com"
    assert cfg.db_path == "test_db.db"
    assert cfg.pdf_dir == "test_pdfs"
