"""
Gmail SMTP 이메일 발송 서비스
- Outlook COM 불필요
- Gmail 앱 비밀번호(App Password)만으로 발송
- 첨부파일(PDF, HWP) 지원
- HTML 본문 지원
"""

import os
import re
import time
import logging
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import date, datetime

logger = logging.getLogger(__name__)

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587  # STARTTLS


class GmailService:
    """
    Gmail SMTP를 통한 이메일 발송 서비스.
    Gmail 앱 비밀번호(App Password) 방식 사용.
    별도 API 키 불필요.
    """

    def __init__(self, sender_email: str, app_password: str, recipient: str):
        """
        Args:
            sender_email: 발신자 Gmail 주소 (예: yourname@gmail.com)
            app_password: Gmail 앱 비밀번호 16자리 (공백 포함/미포함 모두 가능)
            recipient: 수신자 이메일 주소
        """
        self.sender_email = sender_email
        # 앱 비밀번호에서 공백 제거 (xxxx xxxx xxxx xxxx → xxxxxxxxxxxxxxxx)
        self.app_password = app_password.replace(" ", "")
        self.recipient = recipient
        logger.info(f"Gmail 서비스 초기화: {sender_email} -> {recipient}")

    def send_dashboard(
        self,
        subject: str,
        html_body: str,
        attachment_paths: list = None,
    ) -> bool:
        """
        HTML 대시보드 이메일을 Gmail로 발송합니다.

        Args:
            subject: 이메일 제목
            html_body: HTML 형식의 본문
            attachment_paths: 첨부파일 경로 목록 (PDF, HWP 등)

        Returns:
            bool: 발송 성공 여부
        """
        try:
            # 멀티파트 메시지 구성
            msg = MIMEMultipart("related")
            msg["From"] = self.sender_email
            msg["To"] = self.recipient
            msg["Subject"] = subject

            # HTML 본문 첨부
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            # 첨부파일 추가
            attached_count = 0
            if attachment_paths:
                for path in attachment_paths:
                    abs_path = os.path.abspath(path)
                    if not os.path.exists(abs_path):
                        logger.warning(f"첨부파일 없음 (건너뜀): {abs_path}")
                        continue
                    try:
                        self._attach_file(msg, abs_path)
                        attached_count += 1
                        logger.info(f"첨부 추가: {os.path.basename(abs_path)}")
                    except Exception as e:
                        logger.warning(f"첨부 실패 ({os.path.basename(abs_path)}): {e}")

            # Gmail SMTP 연결 및 발송
            logger.info(f"Gmail SMTP 연결 중 ({GMAIL_SMTP_HOST}:{GMAIL_SMTP_PORT})...")
            with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()          # TLS 암호화 시작
                server.ehlo()
                server.login(self.sender_email, self.app_password)
                server.sendmail(
                    from_addr=self.sender_email,
                    to_addrs=[self.recipient],
                    msg=msg.as_string(),
                )

            logger.info(f"[OK] Gmail 발송 완료!")
            logger.info(f"     수신자: {self.recipient}")
            logger.info(f"     제목: {subject}")
            logger.info(f"     첨부: {attached_count}개")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(
                f"Gmail 인증 실패: {e}\n"
                "  -> 앱 비밀번호가 올바른지 확인하세요.\n"
                "  -> 구글 계정의 2단계 인증이 활성화되어 있어야 합니다.\n"
                "  -> https://myaccount.google.com/apppasswords 에서 발급"
            )
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Gmail SMTP 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"이메일 발송 중 예외: {e}", exc_info=True)
            return False

    def _attach_file(self, msg: MIMEMultipart, filepath: str):
        """파일을 이메일에 첨부합니다."""
        filename = os.path.basename(filepath)
        mime_type, _ = mimetypes.guess_type(filepath)
        main_type, sub_type = (mime_type or "application/octet-stream").split("/", 1)

        with open(filepath, "rb") as f:
            part = MIMEBase(main_type, sub_type)
            part.set_payload(f.read())

        encoders.encode_base64(part)

        # 한글 파일명 인코딩 처리
        try:
            filename.encode("ascii")
            part.add_header(
                "Content-Disposition", "attachment", filename=filename
            )
        except UnicodeEncodeError:
            # 한글 파일명은 RFC 2231 인코딩 사용
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=("utf-8", "", filename),
            )

        msg.attach(part)

    def generate_dashboard_html(self, summaries: list, report_date: str = None) -> str:
        """
        BOK 뉴스 요약 데이터를 받아 HTML 대시보드를 생성합니다.
        (기존 outlook_service.py의 HTML 생성 로직과 동일)
        """
        from src.services.outlook_service import OutlookService
        svc = OutlookService.__new__(OutlookService)
        return svc._generate_dashboard_html(summaries, report_date)
