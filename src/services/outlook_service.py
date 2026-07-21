"""
Outlook 이메일 서비스
- create_draft(): 기존 초안 저장 메서드 (기존 BOK경제연구/KDI 파이프라인용)
- send_or_draft(): BOK 뉴스 대시보드 — send_mode에 따라 즉시 발송 또는 초안 저장
- generate_html_body(): 기존 단일 보고서 HTML 템플릿 (기존 파이프라인 유지)
- generate_news_dashboard_html(): BOK 뉴스 복수 자료 통합 대시보드 HTML 템플릿
"""

import os
import sys
import re
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class OutlookService:
    def __init__(self, recipient: str, send_mode: str = "draft"):
        """
        OutlookService를 초기화합니다.

        Args:
            recipient: 수신자 이메일 주소
            send_mode: "send" (즉시 발송) 또는 "draft" (초안 저장)
        """
        self.recipient = recipient
        self.send_mode = send_mode  # "send" | "draft"

    # ------------------------------------------------------------------
    # 기존 메서드 (BOK경제연구/KDI 파이프라인 — 초안 저장)
    # ------------------------------------------------------------------

    def create_draft(self, subject: str, body: str, attachment_paths: list = None) -> bool:
        """
        Outlook에 이메일 초안(Draft)을 저장합니다.
        기존 main.py 파이프라인에서 사용됩니다.
        """
        if sys.platform != "win32":
            logger.warning("Outlook은 Windows에서만 지원됩니다. 로컬 HTML 파일로 저장합니다.")
            return self._save_local_draft(subject, body, attachment_paths)

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
                        logger.warning(f"첨부파일 없음: {path}")

            mail.Save()
            logger.info(f"Outlook 초안 저장 완료: {subject}")
            return True
        except Exception as e:
            logger.error(f"Outlook 초안 저장 오류: {e}", exc_info=True)
            return False

    # ------------------------------------------------------------------
    # 신규 메서드 (BOK 뉴스 대시보드 — 즉시 발송 또는 초안)
    # ------------------------------------------------------------------

    def send_or_draft(self, subject: str, body: str, attachment_paths: list = None) -> bool:
        """
        send_mode 설정에 따라 이메일을 즉시 발송하거나 초안으로 저장합니다.
        BOK 뉴스 대시보드 파이프라인(run_bok_daily.py)에서 사용합니다.
        """
        if sys.platform != "win32":
            logger.warning("Outlook은 Windows에서만 지원됩니다. 로컬 HTML 파일로 저장합니다.")
            return self._save_local_draft(subject, body, attachment_paths)

        try:
            import win32com.client
            import pythoncom
            pythoncom.CoInitialize()

            # 먼저 이미 실행 중인 Outlook에 연결 시도, 없으면 새로 실행
            try:
                outlook = win32com.client.GetActiveObject("Outlook.Application")
                logger.info("기존 Outlook 프로세스에 연결됨")
            except Exception:
                logger.info("Outlook 새로 실행 중...")
                outlook = win32com.client.Dispatch("Outlook.Application")

            mail = outlook.CreateItem(0)
            mail.To = self.recipient
            mail.Subject = subject
            mail.HTMLBody = body

            if attachment_paths:
                for path in attachment_paths:
                    abs_path = os.path.abspath(path)
                    if os.path.exists(abs_path):
                        mail.Attachments.Add(abs_path)
                        logger.info(f"첨부 추가: {os.path.basename(abs_path)}")
                    else:
                        logger.warning(f"첨부파일 없음: {abs_path}")

            if self.send_mode == "send":
                mail.Send()
                logger.info(f"이메일 발송 완료 -> {self.recipient}")
                logger.info(f"   제목: {subject}")
            else:
                mail.Save()
                logger.info(f"✅ 이메일 초안 저장 완료: {subject}")

            return True

        except Exception as e:
            logger.error(f"Outlook 오류 ({self.send_mode}): {e}", exc_info=True)
            # Fallback: 로컬 HTML 저장
            return self._save_local_draft(subject, body, attachment_paths)

    # ------------------------------------------------------------------
    # BOK 뉴스 대시보드 HTML 생성 (복수 자료 통합)
    # ------------------------------------------------------------------

    def generate_news_dashboard_html(
        self,
        summaries: list[dict],
        report_date: str = "",
    ) -> str:
        """
        여러 BOK 뉴스/자료 요약을 하나의 아름다운 HTML 대시보드 이메일로 생성합니다.

        Args:
            summaries: [{"title", "one_line", "summary_bullets", "implication", "keywords",
                          "category", "date", "detail_url"}, ...]
            report_date: 대시보드 날짜 (기본: 오늘)
        """
        if not report_date:
            report_date = datetime.now().strftime("%Y년 %m월 %d일")

        total = len(summaries)
        summarized = sum(1 for s in summaries if s.get("one_line") and "실패" not in s.get("one_line", ""))
        attachments_count = sum(len(s.get("file_paths", [])) for s in summaries)

        # 통계 바
        stats_html = f"""
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:28px;">
          <tr>
            <td width="33%" style="text-align:center; padding:16px 8px; background:#f0f9ff;
                border-radius:10px; margin-right:8px;">
              <div style="font-size:28px; font-weight:800; color:#0369a1; line-height:1;">{total}</div>
              <div style="font-size:12px; color:#64748b; margin-top:4px;">📄 금일 수집 자료</div>
            </td>
            <td width="4px"></td>
            <td width="33%" style="text-align:center; padding:16px 8px; background:#f0fdf4;
                border-radius:10px;">
              <div style="font-size:28px; font-weight:800; color:#15803d; line-height:1;">{summarized}</div>
              <div style="font-size:12px; color:#64748b; margin-top:4px;">🤖 AI 요약 완료</div>
            </td>
            <td width="4px"></td>
            <td width="33%" style="text-align:center; padding:16px 8px; background:#fdf4ff;
                border-radius:10px;">
              <div style="font-size:28px; font-weight:800; color:#7e22ce; line-height:1;">{attachments_count}</div>
              <div style="font-size:12px; color:#64748b; margin-top:4px;">📎 첨부 파일</div>
            </td>
          </tr>
        </table>
        """

        # 자료 카드 생성
        cards_html = ""
        for idx, s in enumerate(summaries, 1):
            cards_html += self._build_report_card(idx, s)

        # 전체 HTML 조합
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BOK 일일 브리핑 {report_date}</title>
</head>
<body style="margin:0; padding:20px 10px; background-color:#eef2f7;
  font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Malgun Gothic', sans-serif;">

  <!-- 외부 래퍼 -->
  <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%"
    style="max-width:660px;">
    <tr><td>

      <!-- =================== 헤더 =================== -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
        style="background:linear-gradient(135deg,#0a1628 0%,#1e3a5f 60%,#0e4d8f 100%);
               border-radius:16px 16px 0 0; overflow:hidden; margin-bottom:0;">
        <tr>
          <td style="padding:36px 40px 28px 40px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td>
                  <div style="font-size:22px; font-weight:800; color:#ffffff; letter-spacing:-0.5px;">
                    🏦 BOK Daily Intelligence
                  </div>
                  <div style="font-size:13px; color:#93c5fd; margin-top:6px;">
                    한국은행 일일 자료 요약 브리핑
                  </div>
                </td>
                <td style="text-align:right; vertical-align:top;">
                  <span style="display:inline-block; background:rgba(255,255,255,0.15);
                    color:#e0f2fe; font-size:12px; font-weight:600;
                    padding:6px 14px; border-radius:20px; white-space:nowrap;">
                    📅 {report_date}
                  </span>
                </td>
              </tr>
              <tr>
                <td colspan="2" style="padding-top:16px;">
                  <div style="font-size:12px; color:#7dd3fc;">
                    From. 자산운용팀 AI 리서치 어시스턴트
                    &nbsp;|&nbsp; 출처: 한국은행 뉴스/자료
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- =================== 본문 =================== -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
        style="background:#ffffff; padding:32px 40px; border-left:1px solid #e2e8f0;
               border-right:1px solid #e2e8f0;">
        <tr>
          <td>
            {stats_html}
            {cards_html}
          </td>
        </tr>
      </table>

      <!-- =================== 푸터 =================== -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
        style="background:#f8fafc; border:1px solid #e2e8f0;
               border-radius:0 0 16px 16px; overflow:hidden;">
        <tr>
          <td style="padding:20px 40px;">
            <p style="margin:0 0 6px 0; font-size:11px; color:#94a3b8; line-height:1.6;">
              ⚠️ 본 브리핑은 AI(Google Gemini)가 자동으로 생성하였습니다.
              투자·여신 결정 전 반드시 원문을 확인하시고 전문가의 판단을 더하십시오.
            </p>
            <p style="margin:0; font-size:11px; color:#cbd5e1;">
              발송 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
              &nbsp;|&nbsp; BOK Daily Intelligence v2.0
            </p>
          </td>
        </tr>
      </table>

    </td></tr>
  </table>
</body>
</html>"""
        return html

    def _build_report_card(self, idx: int, s: dict) -> str:
        """단일 자료 카드 HTML을 생성합니다."""
        title = s.get("title", "제목 없음")
        one_line = s.get("one_line", "")
        bullets = s.get("summary_bullets", [])
        implication = s.get("implication", {})
        keywords = s.get("keywords", [])
        category = s.get("category", "한국은행")
        pub_date = s.get("date", "")
        detail_url = s.get("detail_url", "https://www.bok.or.kr")

        # 핵심 요약 불릿
        bullets_html = ""
        for b in bullets:
            bullets_html += f"""
            <tr>
              <td style="padding:6px 0; vertical-align:top;">
                <table cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="width:20px; vertical-align:top; padding-top:2px;">
                      <div style="width:6px; height:6px; border-radius:50%;
                        background:#3b82f6; margin-top:6px;"></div>
                    </td>
                    <td style="font-size:13px; line-height:1.65; color:#334155;
                        padding-left:6px;">{b}</td>
                  </tr>
                </table>
              </td>
            </tr>"""

        # 시사점 패널
        opportunity = implication.get("opportunity", "")
        risk = implication.get("risk", "")
        action_point = implication.get("action_point", "")

        opp_html = f"""
        <td width="50%" style="vertical-align:top; padding-right:6px;">
          <div style="background:#f0fdf4; border-left:4px solid #22c55e;
              border-radius:0 8px 8px 0; padding:14px;">
            <div style="font-size:12px; font-weight:700; color:#166534; margin-bottom:6px;">
              📈 기회 요인
            </div>
            <div style="font-size:12px; line-height:1.6; color:#14532d;">{opportunity or "해당 없음"}</div>
          </div>
        </td>""" if opportunity else ""

        risk_html = f"""
        <td width="50%" style="vertical-align:top; padding-left:6px;">
          <div style="background:#fef2f2; border-left:4px solid #ef4444;
              border-radius:0 8px 8px 0; padding:14px;">
            <div style="font-size:12px; font-weight:700; color:#991b1b; margin-bottom:6px;">
              ⚠️ 리스크 요인
            </div>
            <div style="font-size:12px; line-height:1.6; color:#7f1d1d;">{risk or "해당 없음"}</div>
          </div>
        </td>""" if risk else ""

        action_html = f"""
        <tr>
          <td colspan="2" style="padding-top:10px;">
            <div style="background:#fffbeb; border-left:4px solid #f59e0b;
                border-radius:0 8px 8px 0; padding:14px;">
              <div style="font-size:12px; font-weight:700; color:#92400e; margin-bottom:4px;">
                🎯 액션 포인트
              </div>
              <div style="font-size:12px; line-height:1.6; color:#78350f;">{action_point}</div>
            </div>
          </td>
        </tr>""" if action_point else ""

        # 키워드 배지
        kw_html = "".join(
            f'<span style="display:inline-block; background:#f1f5f9; color:#475569; '
            f'font-size:11px; font-weight:500; padding:3px 9px; border-radius:9999px; '
            f'margin-right:5px; margin-bottom:5px;">#{kw}</span>'
            for kw in keywords
        )

        return f"""
        <!-- 자료 카드 #{idx} -->
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
          style="border:1px solid #e2e8f0; border-radius:12px; overflow:hidden;
                 margin-bottom:24px; box-shadow:0 1px 3px rgba(0,0,0,0.06);">
          <!-- 카드 헤더 -->
          <tr>
            <td style="padding:16px 20px 12px 20px; border-bottom:1px solid #f1f5f9;
                background:#fafbfc;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td>
                    <span style="display:inline-block; background:#3b82f6; color:#ffffff;
                      font-size:10px; font-weight:700; padding:3px 10px;
                      border-radius:9999px; margin-bottom:8px;">{category}</span>
                    {'<span style="display:inline-block; font-size:10px; color:#94a3b8; margin-left:8px;">📅 ' + pub_date + '</span>' if pub_date else ''}
                  </td>
                </tr>
                <tr>
                  <td style="font-size:15px; font-weight:700; color:#0f172a;
                      line-height:1.4;">{title}</td>
                </tr>
                {('<tr><td style="font-size:12px; color:#3b82f6; font-weight:600; '
                   'padding-top:6px; font-style:italic;">' + one_line + '</td></tr>') if one_line else ''}
              </table>
            </td>
          </tr>
          <!-- 핵심 요약 -->
          <tr>
            <td style="padding:16px 20px 8px 20px;">
              <div style="font-size:12px; font-weight:700; color:#0f172a;
                  text-transform:uppercase; letter-spacing:0.05em; margin-bottom:10px;
                  padding-bottom:6px; border-bottom:2px solid #3b82f6; display:inline-block;">
                💡 핵심 요약
              </div>
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                {bullets_html}
              </table>
            </td>
          </tr>
          <!-- 시사점 패널 -->
          <tr>
            <td style="padding:8px 20px 16px 20px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  {opp_html}
                  {risk_html}
                </tr>
                {action_html}
              </table>
            </td>
          </tr>
          <!-- 키워드 + 원문 버튼 -->
          <tr>
            <td style="padding:12px 20px 16px 20px; background:#f8fafc;
                border-top:1px solid #f1f5f9;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="vertical-align:middle;">
                    {kw_html}
                  </td>
                  <td style="text-align:right; vertical-align:middle; white-space:nowrap;">
                    <a href="{detail_url}"
                      style="display:inline-block; background:#1e3a5f; color:#ffffff;
                             font-size:11px; font-weight:600; padding:7px 16px;
                             border-radius:6px; text-decoration:none;">
                      원문 보기 →
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
        """

    # ------------------------------------------------------------------
    # 기존 단일 보고서 HTML 템플릿 (BOK경제연구/KDI 파이프라인용)
    # ------------------------------------------------------------------

    def generate_html_body(
        self,
        source: str,
        title: str,
        summary: list,
        implication: dict,
        keywords: list,
        pdf_name: str,
    ) -> str:
        """기존 단일 보고서 이메일 HTML 템플릿입니다. (기존 파이프라인 유지)"""
        summary_items_html = ""
        for item in summary:
            summary_items_html += f"""
            <li style="margin-bottom: 12px; padding-left: 16px; position: relative;
                font-size: 14px; line-height: 1.6; color: #334155;
                border-left: 3px solid #3b82f6;">
                {item}
            </li>"""

        keywords_html = ""
        for keyword in keywords:
            keywords_html += f"""
            <span style="display: inline-block; background-color: #f1f5f9; color: #475569;
                font-size: 12px; font-weight: 500; padding: 4px 10px;
                border-radius: 9999px; margin-right: 6px; margin-bottom: 6px;">
                #{keyword}
            </span>"""

        upside_risk = implication.get("upside_risk") or "N/A"
        downside_risk = implication.get("downside_risk") or "N/A"

        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; padding:20px; background-color:#f8fafc;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%"
    style="max-width:600px; background:#ffffff; border-radius:12px;
           box-shadow:0 4px 6px -1px rgba(0,0,0,0.1); border:1px solid #e2e8f0;">
    <tr>
      <td style="padding:35px 40px; background:linear-gradient(135deg,#1e3a8a 0%,#3b82f6 100%);
          color:#ffffff; border-radius:12px 12px 0 0;">
        <span style="font-size:12px; font-weight:600; text-transform:uppercase;
          background:rgba(255,255,255,0.2); padding:4px 8px; border-radius:4px;
          display:inline-block; margin-bottom:12px;">{source}</span>
        <h1 style="margin:0; font-size:24px; font-weight:700; line-height:1.3;">{title}</h1>
      </td>
    </tr>
    <tr>
      <td style="padding:40px 40px 30px 40px;">
        <h2 style="margin-top:0; margin-bottom:16px; font-size:16px; font-weight:600;
            color:#0f172a; border-bottom:2px solid #3b82f6; padding-bottom:8px;
            display:inline-block;">핵심 요약 (Executive Summary)</h2>
        <ul style="margin:0 0 28px 0; padding-left:0; list-style-type:none;">
            {summary_items_html}
        </ul>
        <h2 style="margin-top:0; margin-bottom:16px; font-size:16px; font-weight:600;
            color:#0f172a;">상황분석 및 시사점</h2>
        <div style="margin-bottom:16px; padding:16px; background:#f0fdf4;
            border-left:4px solid #22c55e; border-radius:0 8px 8px 0;">
          <h3 style="margin:0 0 6px; font-size:14px; font-weight:600; color:#166534;">
            📈 Upside Risk (기회 요인)</h3>
          <p style="margin:0; font-size:14px; line-height:1.5; color:#1b4332;">{upside_risk}</p>
        </div>
        <div style="margin-bottom:28px; padding:16px; background:#fef2f2;
            border-left:4px solid #ef4444; border-radius:0 8px 8px 0;">
          <h3 style="margin:0 0 6px; font-size:14px; font-weight:600; color:#991b1b;">
            ⚠️ Downside Risk (위험 요인)</h3>
          <p style="margin:0; font-size:14px; line-height:1.5; color:#7f1d1d;">{downside_risk}</p>
        </div>
        <h2 style="margin-top:0; margin-bottom:12px; font-size:14px; font-weight:600;
            color:#0f172a;">관련 키워드</h2>
        <div style="margin-bottom:28px;">{keywords_html}</div>
      </td>
    </tr>
    <tr>
      <td style="padding:20px 40px; background:#f8fafc; border-top:1px solid #e2e8f0;
          font-size:12px; color:#64748b; line-height:1.5; border-radius:0 0 12px 12px;">
        <p style="margin:0 0 4px;"><strong>첨부 파일:</strong> {pdf_name}</p>
        <p style="margin:0;">본 이메일은 금융 규제 모니터링 시스템에 의해 자동 생성된 임시 보관 메일입니다.</p>
      </td>
    </tr>
  </table>
</body>
</html>"""

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _save_local_draft(self, subject: str, body: str, attachment_paths: list = None) -> bool:
        """이메일 내용을 로컬 HTML 파일로 저장합니다. (Windows 외 환경 fallback)"""
        try:
            os.makedirs("data/drafts", exist_ok=True)
            safe_subject = re.sub(r'[\\/*?"<>|]', "", subject).strip()[:50]
            filename = f"draft_{safe_subject}_{int(time.time())}.html"
            filepath = os.path.join("data/drafts", filename)

            if attachment_paths:
                att_info = "<hr style='border:1px solid #e2e8f0; margin-top:20px;'>"
                att_info += "<div style='padding:10px; background:#f1f5f9; border-radius:4px; font-size:12px; color:#475569;'>"
                att_info += "<strong>[첨부파일 대기]</strong><ul>"
                for path in attachment_paths:
                    att_info += f"<li>{os.path.basename(path)} ({path})</li>"
                att_info += "</ul></div>"
                # re.sub 대체 문자열에 \U 등 escape가 있으면 오류 → lambda 사용
                body = re.sub(
                    r"(?i)</body>",
                    lambda m: att_info + "</body>",
                    body,
                    count=1
                ) or body + att_info

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(body)
            logger.info(f"로컬 초안 저장: {filepath}")
            return True
        except Exception as e:
            logger.error(f"로컬 초안 저장 실패: {e}", exc_info=True)
            return False
