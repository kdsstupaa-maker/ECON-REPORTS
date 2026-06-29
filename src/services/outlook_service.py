import os
import sys
import re
import time
import logging

logger = logging.getLogger(__name__)

class OutlookService:
    def __init__(self, recipient: str):
        """
        Initialize OutlookService with a default recipient.
        """
        self.recipient = recipient

    def create_draft(self, subject: str, body: str, attachment_paths: list = None) -> bool:
        """
        Creates an email draft in Outlook with the given subject, HTML body, and optional attachments.
        If not on Windows, falls back to writing the HTML draft locally under 'data/drafts/'.
        """
        if sys.platform != "win32":
            logger.warning("Outlook integration is only supported on Windows. Falling back to local draft file.")
            return self._save_local_draft(subject, body)

        try:
            import win32com.client
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)
            mail.To = self.recipient
            mail.Subject = subject
            mail.HTMLBody = body

            if attachment_paths:
                for path in attachment_paths:
                    if os.path.exists(path):
                        mail.Attachments.Add(os.path.abspath(path))
                    else:
                        logger.warning(f"Attachment file not found: {path}")

            mail.Save()
            return True
        except Exception as e:
            logger.error(f"Error creating Outlook draft: {e}", exc_info=True)
            return False

    def _save_local_draft(self, subject: str, body: str) -> bool:
        """
        Saves the email draft as a local HTML file under 'data/drafts/' as a fallback.
        """
        try:
            os.makedirs("data/drafts", exist_ok=True)
            # Sanitize subject to be a safe filename
            sanitized_subject = re.sub(r'[\\/*?:"<>| ]', '_', subject)
            filename = f"draft_{sanitized_subject}_{int(time.time())}.html"
            filepath = os.path.join("data/drafts", filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(body)
            logger.info(f"Fallback draft saved locally: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save fallback draft: {e}", exc_info=True)
            return False

    def generate_html_body(
        self,
        source: str,
        title: str,
        summary: list,
        implication: dict,
        keywords: list,
        pdf_name: str
    ) -> str:
        """
        Generates a beautiful, responsive HTML email template using inline CSS.
        """
        summary_items_html = ""
        for item in summary:
            summary_items_html += f"""
            <li style="margin-bottom: 12px; padding-left: 16px; position: relative; font-size: 14px; line-height: 1.6; color: #334155; border-left: 3px solid #3b82f6;">
                {item}
            </li>"""

        keywords_html = ""
        for keyword in keywords:
            keywords_html += f"""
            <span style="display: inline-block; background-color: #f1f5f9; color: #475569; font-size: 12px; font-weight: 500; padding: 4px 10px; border-radius: 9999px; margin-right: 6px; margin-bottom: 6px;">
                #{keyword}
            </span>"""

        upside_risk = implication.get("upside_risk", "N/A")
        downside_risk = implication.get("downside_risk", "N/A")

        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 20px; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
    <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border: 1px solid #e2e8f0; overflow: hidden; border-collapse: separate;">
        <!-- Header -->
        <tr>
            <td style="padding: 35px 40px; background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: #ffffff;">
                <span style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; background-color: rgba(255, 255, 255, 0.2); padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 12px;">{source}</span>
                <h1 style="margin: 0; font-size: 24px; font-weight: 700; line-height: 1.3; letter-spacing: -0.02em;">{title}</h1>
            </td>
        </tr>
        <!-- Content Area -->
        <tr>
            <td style="padding: 40px 40px 30px 40px;">
                <!-- Executive Summary Section -->
                <h2 style="margin-top: 0; margin-bottom: 16px; font-size: 16px; font-weight: 600; color: #0f172a; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; display: inline-block;">핵심 요약 (Executive Summary)</h2>
                <ul style="margin: 0 0 28px 0; padding-left: 0; list-style-type: none;">
                    {summary_items_html}
                </ul>

                <!-- Implications Section -->
                <h2 style="margin-top: 0; margin-bottom: 16px; font-size: 16px; font-weight: 600; color: #0f172a;">상황분석 및 시사점</h2>
                
                <!-- Upside Risk Panel -->
                <div style="margin-bottom: 16px; padding: 16px; background-color: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 0 8px 8px 0;">
                    <h3 style="margin-top: 0; margin-bottom: 6px; font-size: 14px; font-weight: 600; color: #166534;">📈 Upside Risk (기회 요인)</h3>
                    <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #1b4332;">{upside_risk}</p>
                </div>

                <!-- Downside Risk Panel -->
                <div style="margin-bottom: 28px; padding: 16px; background-color: #fef2f2; border-left: 4px solid #ef4444; border-radius: 0 8px 8px 0;">
                    <h3 style="margin-top: 0; margin-bottom: 6px; font-size: 14px; font-weight: 600; color: #991b1b;">⚠️ Downside Risk (위험 요인)</h3>
                    <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #7f1d1d;">{downside_risk}</p>
                </div>

                <!-- Keywords Section -->
                <h2 style="margin-top: 0; margin-bottom: 12px; font-size: 14px; font-weight: 600; color: #0f172a;">관련 키워드</h2>
                <div style="margin-bottom: 28px;">
                    {keywords_html}
                </div>
            </td>
        </tr>
        <!-- Footer -->
        <tr>
            <td style="padding: 20px 40px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; line-height: 1.5;">
                <p style="margin: 0 0 4px 0;"><strong>첨부 파일:</strong> {pdf_name}</p>
                <p style="margin: 0;">본 이메일은 금융 규제 모니터링 시스템에 의해 자동 생성된 임시 보관 메일입니다.</p>
            </td>
        </tr>
    </table>
</body>
</html>"""
        return html_template
