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

def test_config_env_override(tmp_path, monkeypatch):
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
    monkeypatch.setenv("GEMINI_API_KEY", "OVERRIDDEN_KEY")
    cfg = Config(config_file)
    assert cfg.gemini_key == "OVERRIDDEN_KEY"

def test_config_missing_file():
    with pytest.raises(RuntimeError) as excinfo:
        Config("nonexistent_config.yaml")
    assert "Config file not found" in str(excinfo.value)

def test_config_missing_key(tmp_path):
    config_file = os.path.join(tmp_path, "config.yaml")
    with open(config_file, "w", encoding="utf-8") as f:
        f.write("""
gemini:
  model: "gemini-1.5-flash"
email:
  recipient: "test@example.com"
storage:
  db_path: "test_db.db"
  pdf_dir: "test_pdfs"
""")
    with pytest.raises(RuntimeError) as excinfo:
        Config(config_file)
    assert "Missing required config key" in str(excinfo.value)

