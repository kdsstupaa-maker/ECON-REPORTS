"""
Gemini AI 요약 서비스
공식 SDK: google-genai (최신)
문서: https://googleapis.github.io/python-genai/
설치: pip install google-genai

- summarize_news_pdf(): BOK 뉴스/자료 요약 (자산운용·여신 관점)
- summarize_pdf(): 기존 BOK경제연구/KDI 보고서 요약 (신용리스크 관점)
- summarize_text(): 텍스트 기반 요약 (PDF 없을 때)
"""

import os
import io
import json
import time
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# 현재 최신 모델 (google-genai 공식 문서 기준)
DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiSummarizer:

    def __init__(self, api_key: str, model_name: str = DEFAULT_MODEL):
        """
        google-genai SDK로 Gemini 클라이언트를 초기화합니다.
        ref: https://googleapis.github.io/python-genai/
        """
        self.model_name = model_name
        # 공식 문서 권장 방식: genai.Client(api_key=...)
        self.client = genai.Client(api_key=api_key)
        logger.info(f"Gemini 클라이언트 초기화 완료 (모델: {model_name})")

    # ------------------------------------------------------------------
    # [주 메서드] BOK 뉴스/자료 — 자산운용·여신 관점 요약
    # ------------------------------------------------------------------

    def summarize_news_pdf(self, pdf_path: str, title: str = "") -> dict:
        """
        BOK 뉴스/자료 PDF를 자산운용·여신 관점으로 요약합니다.

        공식 문서 파일 업로드 패턴 사용:
          file = client.files.upload(file='path/to/file.pdf')
          response = client.models.generate_content(
              model='gemini-2.5-flash',
              contents=['prompt', file]
          )

        반환 구조:
        {
          "title": str,
          "one_line": str,
          "summary_bullets": [str, str, str],
          "implication": {"opportunity": str, "risk": str, "action_point": str},
          "keywords": [str, ...]
        }
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 파일 없음: {pdf_path}")

        logger.info(f"Gemini 파일 업로드: {os.path.basename(pdf_path)}")

        # 한글 파일명 인코딩 오류 방지: 파일을 bytes로 읽어 업로드
        with open(pdf_path, "rb") as f:
            file_bytes = f.read()

        # 업로드 시 display_name과 mime_type 명시
        uploaded_file = self.client.files.upload(
            file=io.BytesIO(file_bytes),
            config=types.UploadFileConfig(
                mime_type="application/pdf",
                display_name=os.path.basename(pdf_path),
            ),
        )

        try:
            # 2) 파일 처리 완료 대기
            self._wait_for_active(uploaded_file)

            # 3) 프롬프트 구성
            title_hint = f"문서 제목: {title}\n\n" if title else ""
            prompt = (
                "당신은 30년 경력 자산운용 전문가 팀의 금융 리서치 어시스턴트입니다.\n"
                "첨부된 한국은행 자료를 아래 4가지 관점에서 분석하여 JSON으로 요약하세요.\n\n"
                "분석 관점:\n"
                "1. 거시경제(GDP, 물가, 금리, 환율) 동향이 포트폴리오에 미치는 영향\n"
                "2. 여신·신용 리스크 시사점 (기업/가계부채, 연체율, 대손충당금)\n"
                "3. 채권·주식·부동산·외환시장 파급효과\n"
                "4. 통화정책·거시건전성 정책이 자산운용 전략에 주는 시사점\n\n"
                + title_hint
                + "아래 JSON 형식으로만 응답하세요 (한국어):\n"
                "{\n"
                '  "title": "보고서 제목",\n'
                '  "one_line": "30자 이내 핵심 한 줄 요약",\n'
                '  "summary_bullets": [\n'
                '    "거시경제 관점 핵심 포인트",\n'
                '    "여신/신용리스크 관점 핵심 포인트",\n'
                '    "시장/정책 관점 핵심 포인트"\n'
                "  ],\n"
                '  "implication": {\n'
                '    "opportunity": "자산운용 기회 요인",\n'
                '    "risk": "주요 위협·리스크 요인",\n'
                '    "action_point": "실무 담당자 즉각 액션 포인트"\n'
                "  },\n"
                '  "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]\n'
                "}\n"
                "JSON 외 텍스트는 절대 포함하지 마세요."
            )

            # 4) 콘텐츠 생성 (공식 문서 권장: contents=['text', file])
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, uploaded_file],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            # 5) JSON 파싱
            try:
                result = json.loads(response.text)
                if not result.get("title") and title:
                    result["title"] = title
                logger.info(f"요약 완료: {result.get('one_line', '')[:50]}")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 파싱 실패, fallback 반환: {e}")
                return self._build_fallback(title or os.path.basename(pdf_path))

        finally:
            # 업로드 파일 정리
            try:
                self.client.files.delete(name=uploaded_file.name)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # 텍스트 기반 요약 (PDF 없을 때)
    # ------------------------------------------------------------------

    def summarize_text(self, text: str, title: str = "") -> dict:
        """제목/텍스트 기반 요약 (PDF 첨부 없이 텍스트만으로 요약)."""
        prompt = (
            "당신은 30년 경력 자산운용 전문가 팀의 금융 리서치 어시스턴트입니다.\n"
            "아래 내용을 자산운용·여신 관점에서 분석하여 JSON으로 요약하세요.\n\n"
            f"제목: {title}\n내용: {text[:4000]}\n\n"
            "JSON 형식 (한국어):\n"
            "{\n"
            '  "title": "제목",\n'
            '  "one_line": "30자 이내 한 줄 요약",\n'
            '  "summary_bullets": ["포인트1", "포인트2", "포인트3"],\n'
            '  "implication": {\n'
            '    "opportunity": "기회 요인",\n'
            '    "risk": "위협 요인",\n'
            '    "action_point": "액션 포인트"\n'
            "  },\n"
            '  "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]\n'
            "}"
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return self._build_fallback(title)

    # ------------------------------------------------------------------
    # 기존 파이프라인 호환 (BOK경제연구/KDI — 신용리스크 관점)
    # ------------------------------------------------------------------

    def summarize_pdf(self, pdf_path: str) -> dict:
        """기존 BOK경제연구/KDI 파이프라인 호환 메서드. (신용리스크 심사 관점)"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 파일 없음: {pdf_path}")

        with open(pdf_path, "rb") as f:
            file_bytes = f.read()
        uploaded_file = self.client.files.upload(
            file=io.BytesIO(file_bytes),
            config=types.UploadFileConfig(
                mime_type="application/pdf",
                display_name=os.path.basename(pdf_path),
            ),
        )

        try:
            self._wait_for_active(uploaded_file)

            prompt = (
                "You are an insurance company credit risk auditor. "
                "Analyze the provided PDF and output ONLY valid JSON:\n"
                "{\n"
                '  "title": "Title in Korean",\n'
                '  "summary": ["point1 in Korean", "point2 in Korean", "point3 in Korean"],\n'
                '  "implication": {\n'
                '    "upside_risk": "opportunity in Korean",\n'
                '    "downside_risk": "risk in Korean"\n'
                "  },\n"
                '  "keywords": ["kw1", "kw2", "kw3"]\n'
                "}"
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, uploaded_file],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            try:
                return json.loads(response.text)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON 파싱 실패: {e}") from e

        finally:
            try:
                self.client.files.delete(name=uploaded_file.name)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _wait_for_active(self, uploaded_file, max_wait: int = 300):
        """
        Gemini 파일 처리(PROCESSING -> ACTIVE) 완료를 대기합니다.
        max_wait: 최대 대기 초 (기본 300초)
        """
        waited = 0
        while waited < max_wait:
            info = self.client.files.get(name=uploaded_file.name)
            state = info.state.name if hasattr(info.state, "name") else str(info.state)
            if state == "ACTIVE":
                return
            elif state == "FAILED":
                raise ValueError(f"Gemini 파일 처리 실패: {uploaded_file.name}")
            time.sleep(2)
            waited += 2

        raise TimeoutError(f"Gemini 파일 처리 타임아웃 ({max_wait}초): {uploaded_file.name}")

    def _build_fallback(self, title: str) -> dict:
        """요약 실패 시 반환할 기본 구조."""
        return {
            "title": title,
            "one_line": "AI 요약 생성 실패 — 원문 확인 필요",
            "summary_bullets": ["PDF 분석에 실패했습니다. 첨부 원문을 직접 확인해 주세요."],
            "implication": {
                "opportunity": "분석 실패",
                "risk": "분석 실패",
                "action_point": "원문 파일을 직접 검토해 주세요.",
            },
            "keywords": ["한국은행", "자료"],
        }
