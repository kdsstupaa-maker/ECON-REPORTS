from abc import ABC, abstractmethod
import os
import requests

class BaseCrawler(ABC):
    def __init__(self, pdf_dir):
        self.pdf_dir = pdf_dir
        os.makedirs(self.pdf_dir, exist_ok=True)

    @abstractmethod
    def fetch_latest_reports(self):
        """최신 보고서들의 목록을 딕셔너리 리스트로 반환합니다.
        반환 데이터 규격: [{'key': str, 'title': str, 'pdf_url': str, 'author': str, 'date': str}]
        """
        pass

    def download_pdf(self, url, folder_name, filename):
        target_dir = os.path.join(self.pdf_dir, folder_name)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)
        return os.path.abspath(file_path)
