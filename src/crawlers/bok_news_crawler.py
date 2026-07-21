"""
BOK 뉴스/자료 크롤러
대상: https://www.bok.or.kr/portal/singl/newsData/list.do?menuNo=201150

실제 데이터는 Ajax API (/portal/singl/newsData/listCont.do) 로 로드됩니다.
이 크롤러는 해당 API를 직접 호출하여 게시판 목록을 수집합니다.
"""

import os
import re
import time
import logging
import urllib.parse
import requests
from bs4 import BeautifulSoup
from datetime import date

logger = logging.getLogger(__name__)

BASE_URL = "https://www.bok.or.kr"
LIST_CONT_URL = f"{BASE_URL}/portal/singl/newsData/listCont.do"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html, */*; q=0.01",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE_URL}/portal/singl/newsData/list.do?menuNo=201150&sort=1&pageUnit=10",
}


class BOKNewsCrawler:
    """한국은행 뉴스/자료 크롤러 (Ajax API 직접 호출 방식)"""

    def __init__(self, pdf_dir: str, today_only: bool = True, max_items: int = 10):
        self.pdf_dir = pdf_dir
        self.today_only = today_only
        self.max_items = max_items
        os.makedirs(self.pdf_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # 공개 메서드
    # ------------------------------------------------------------------

    def fetch_today_news(self) -> list:
        """
        오늘 날짜(today_only=True) 또는 최신 N건의 BOK 뉴스/자료 목록을 반환합니다.

        반환 구조:
        [
            {
                "key": str,          # bok_news_<nttId>
                "title": str,
                "date": str,         # YYYY-MM-DD
                "category": str,
                "detail_url": str,
                "attachments": [{"name", "url", "ext"}, ...],
            }, ...
        ]
        """
        logger.info("BOK 뉴스/자료 목록 수집 시작 (Ajax API)...")
        raw_items = self._fetch_list()
        logger.info(f"API에서 {len(raw_items)}건 파싱됨")

        if self.today_only:
            today_str = date.today().strftime("%Y-%m-%d")
            filtered = [r for r in raw_items if r.get("date") == today_str]
            logger.info(f"오늘 날짜({today_str}) 자료: {len(filtered)}건")
            if not filtered:
                logger.warning("오늘 자료 없음 → 최신 5건으로 fallback")
                filtered = raw_items[:5]
        else:
            filtered = raw_items[: self.max_items]

        # 각 게시물의 상세 페이지에서 첨부파일 수집
        results = []
        for item in filtered:
            try:
                attachments = self._fetch_attachments(item["detail_url"])
                item["attachments"] = attachments
                logger.info(f"  첨부파일 {len(attachments)}개 — {item['title'][:40]}")
                results.append(item)
                time.sleep(1)  # 서버 부하 방지
            except Exception as e:
                logger.warning(f"  첨부파일 수집 실패 ({item['title'][:30]}): {e}")
                item["attachments"] = []
                results.append(item)

        logger.info(f"최종 처리 대상: {len(results)}건")
        return results

    def download_attachments(self, item: dict) -> list:
        """
        게시물의 첨부파일(PDF 우선, HWP 차선)을 다운로드하고
        로컬 파일 경로 목록을 반환합니다.
        """
        saved_paths = []
        date_str = item.get("date", "").replace("-", "")
        safe_title = re.sub(r'[\\/*?"<>|:\s]', "_", item.get("title", "unknown"))[:40]
        folder = os.path.join(self.pdf_dir, "BOK_NEWS", date_str)
        os.makedirs(folder, exist_ok=True)

        attachments = item.get("attachments", [])
        pdf_list = [a for a in attachments if a["ext"].lower() == "pdf"]
        hwp_list = [a for a in attachments if a["ext"].lower() in ("hwp", "hwpx")]
        targets = pdf_list if pdf_list else hwp_list

        if not targets:
            logger.warning(f"다운로드 가능한 첨부파일 없음: {item['title'][:40]}")
            return []

        for att in targets:
            ext = att["ext"].lower()
            filename = f"{safe_title}.{ext}"
            filepath = os.path.join(folder, filename)

            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                logger.info(f"기존 파일 재사용: {filename}")
                saved_paths.append(os.path.abspath(filepath))
                continue

            try:
                resp = self._get_with_retry(att["url"], stream=True, timeout=120)
                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                file_size = os.path.getsize(filepath)
                if file_size > 0:
                    saved_paths.append(os.path.abspath(filepath))
                    logger.info(f"다운로드 완료: {filename} ({file_size:,} bytes)")
                else:
                    logger.warning(f"빈 파일 다운로드됨: {filename}")
                    os.remove(filepath)
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"다운로드 실패 ({att['name'][:40]}): {e}")

        return saved_paths

    # ------------------------------------------------------------------
    # 내부 메서드
    # ------------------------------------------------------------------

    def _fetch_list(self) -> list:
        """BOK Ajax API를 호출하여 게시물 목록을 파싱합니다."""
        params = {
            "pageIndex": "1",
            "menuNo": "201150",
            "syncMenuChekKey": "1",
            "searchCnd": "1",
            "searchKwd": "",
            "sort": "1",
            "pageUnit": str(self.max_items),
            "sdate": "",
            "edate": "",
        }

        resp = self._get_with_retry(LIST_CONT_URL, params=params, timeout=30)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        rows = soup.find_all("li", class_="bbsRowCls")
        logger.info(f"bbsRowCls 행 발견: {len(rows)}개")

        items = []
        for row in rows:
            item = self._parse_row(row)
            if item:
                items.append(item)

        return items

    def _parse_row(self, row) -> dict:
        """단일 li.bbsRowCls 행에서 기본 정보를 추출합니다."""
        # 제목 및 링크
        a_tag = row.find("a", class_="title")
        if not a_tag:
            return None

        title = a_tag.get_text(strip=True)
        if not title:
            return None

        href = a_tag.get("href", "")
        detail_url = urllib.parse.urljoin(BASE_URL, href)

        # nttId 추출 → 고유 키
        parsed = urllib.parse.urlparse(href)
        params = urllib.parse.parse_qs(parsed.query)
        ntt_id = (params.get("nttId", [""]))[0]
        key = f"bok_news_{ntt_id}" if ntt_id else f"bok_news_{hash(href)}"

        # 날짜 추출 (span.date)
        date_str = ""
        date_el = row.find("span", class_="date")
        if date_el:
            # sr-only 스팬 제거
            for sr in date_el.find_all("span", class_="sr-only"):
                sr.decompose()
            raw_date = date_el.get_text(strip=True)
            date_str = self._normalize_date(raw_date)

        # 카테고리 (span.depart — 부서명 또는 자료 유형)
        category = "한국은행 뉴스/자료"
        depart_el = row.find("span", class_="depart")
        if depart_el:
            for sr in depart_el.find_all("span", class_="sr-only"):
                sr.decompose()
            cat_text = depart_el.get_text(strip=True)
            if cat_text and cat_text != "...":
                category = cat_text

        # 자료 유형 배지 (span.t1 또는 span.i)
        type_el = row.find("span", class_="t1") or row.find("span", class_="i")
        if type_el:
            type_text = type_el.get_text(strip=True)
            if type_text:
                category = type_text

        return {
            "key": key,
            "title": title,
            "date": date_str,
            "category": category,
            "detail_url": detail_url,
            "ntt_id": ntt_id,
        }

    def _fetch_attachments(self, detail_url: str) -> list:
        """상세 페이지에서 첨부파일 링크 목록을 추출합니다."""
        resp = self._get_with_retry(detail_url, timeout=20)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        attachments = []

        # 첨부파일 다운로드 링크 탐색 (BOK 포털의 다양한 패턴)
        selectors = [
            "a.btn-file",
            "a.i-download",
            "a.file-down",
            "a[href*='fileDown']",
            "a[href*='.pdf']",
            "a[href*='.hwp']",
            "a[class*='download']",
            "a[class*='attach']",
        ]

        seen_urls = set()
        for sel in selectors:
            for link in soup.select(sel):
                href = link.get("href", "")
                if not href or href == "#":
                    continue

                # JavaScript URL 처리
                if href.startswith("javascript"):
                    onclick = link.get("onclick", "")
                    url_m = re.search(r"['\"]([^'\"]+\.(pdf|hwp|hwpx))['\"]", onclick, re.I)
                    if url_m:
                        href = url_m.group(1)
                    else:
                        continue

                full_url = urllib.parse.urljoin(BASE_URL, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                ext = self._guess_ext(href)
                if not ext:
                    # Content-Disposition에서 파일명 추정
                    ext = "pdf"  # 기본값

                name = link.get_text(strip=True) or os.path.basename(href)
                if not name:
                    name = f"첨부파일.{ext}"

                attachments.append({"name": name, "url": full_url, "ext": ext})

        return attachments

    def _guess_ext(self, url: str) -> str:
        """URL에서 파일 확장자를 추출합니다."""
        m = re.search(r'\.(pdf|hwp|hwpx)(?:[?#&]|$)', url, re.I)
        return m.group(1).lower() if m else ""

    def _normalize_date(self, raw: str) -> str:
        """다양한 날짜 포맷을 YYYY-MM-DD로 정규화합니다."""
        raw = raw.strip().rstrip(".")
        m = re.search(r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', raw)
        if m:
            y, mo, d = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
            return f"{y}-{mo}-{d}"
        return raw

    def _get_with_retry(self, url: str, max_retries: int = 3, **kwargs) -> requests.Response:
        """재시도 로직이 포함된 GET 요청을 수행합니다."""
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(url, headers=HEADERS, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                logger.warning(f"요청 실패 (시도 {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                else:
                    raise
