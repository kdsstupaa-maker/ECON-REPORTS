# 금융 보고서 모니터링 및 자동 요약 에이전트 (Financial Reports Monitoring Agent)

이 에이전트는 한국은행(BOK) 경제연구원 및 KDI(한국개발연구원)에서 발표하는 최신 경제/금융 연구 보고서를 자동으로 크롤링하고, Google Gemini LLM을 사용하여 보고서 요약 및 위험 분석(Credit Risk Auditing Perspective)을 수행한 후, 담당자에게 Outlook 이메일 초안(Draft)을 자동으로 생성하고 이력을 로컬 SQLite 데이터베이스에 기록하는 자동화 시스템입니다.

---

## 🛠️ 주요 기능

1. **최신 보고서 자동 크롤링 (Crawling)**
   - 한국은행 경제연구실 게시판 및 KDI 연구자료(Focus) 게시판에서 최신 PDF 보고서를 감지하여 다운로드합니다.
2. **중복 유효성 검사 (Duplication Check)**
   - 다운로드한 보고서의 고유 식별자(Key)를 로컬 SQLite DB와 비교하여 이미 처리된 보고서는 중복 실행하지 않고 건너뜁니다.
3. **Gemini AI 요약 및 시사점 분석 (AI Summarization)**
   - Google Gemini API (`gemini-1.5-flash`)를 활용하여 보험사 신용리스크 심사역(Credit Risk Auditor) 관점에서의 보고서 요약, 기회 요인(Upside Risk), 위협 요인(Downside Risk), 키워드를 한국어 JSON 형태로 추출합니다.
4. **Outlook 이메일 초안 자동 생성 (Outlook Integration)**
   - 분석 완료된 리포트 내용을 바탕으로 수려한 반응형 HTML 템플릿의 이메일 초안을 MS Outlook에 자동 등록하며, 원본 PDF 파일을 첨부합니다. (Windows 외 플랫폼에서는 로컬 HTML 파일 생성으로 대체 작동)
5. **이력 DB 저장 (SQLite Storage)**
   - 처리된 보고서의 메타데이터, LLM 요약 본문, 초안 생성 일시 등을 데이터베이스에 영구 보존합니다.

---

## 📋 설치 및 요구사항 (Installation)

### 1. 시스템 요구사항
- **OS**: Windows 10 이상 권장 (Outlook 연동용, 그 외 OS에서는 로컬 Fallback 작동)
- **Python**: Python 3.12 이상
- **소프트웨어**: Microsoft Outlook (초안 생성 목적)

### 2. 패키지 설치
프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 필수 패키지를 설치합니다.
```bash
pip install -r requirements.txt
```

---

## ⚙️ 환경 설정 (Configuration)

### 1. 설정 파일 작성 (`config/config.yaml`)
`config/` 디렉토리 하위에 `config.yaml` 파일을 생성하고 아래와 같이 채워 넣습니다.
```yaml
gemini:
  api_key: ""              # (선택) Gemini API 키. 환경 변수 설정 시 비워두어도 됩니다.
  model: "gemini-1.5-flash"

email:
  recipient: "your-email@insurance.com" # Outlook 초안의 기본 수신자 주소

storage:
  db_path: "data/reports.db"            # SQLite DB 파일 경로
  pdf_dir: "data/pdfs"                  # 다운로드된 PDF 파일 저장 경로
```

### 2. 환경 변수 설정
보안을 위해 Gemini API Key는 환경 변수로 등록하여 사용하는 것을 권장합니다.
- **Windows (PowerShell)**:
  ```powershell
  $env:GEMINI_API_KEY="your-gemini-api-key-here"
  ```
- **Windows (CMD)**:
  ```cmd
  set GEMINI_API_KEY=your-gemini-api-key-here
  ```

---

## 🚀 실행 및 테스트 방법 (Usage & Testing)

### 1. 수동 실행 (Manual Run)
에이전트를 직접 수동으로 가동하여 보고서 크롤링 및 메일 초안을 생성하려면 아래 명령어를 실행합니다.
```bash
python src/main.py
```

### 2. 테스트 실행 (Test Execution)
전체 단위 테스트 및 통합 테스트를 수행하여 프로그램의 정합성을 검증합니다.
```bash
python -m pytest
```

---

## ⏰ Windows 작업 스케줄러 등록 방법 (Automation Guide)

매일 정해진 시간(예: 매일 오전 9시)에 본 에이전트가 자동으로 실행되어 최신 리포트를 수집하도록 Windows 작업 스케줄러를 등록하는 방법입니다.

### 1단계: 실행 배치 파일(`run_agent.bat`) 작성
프로젝트 루트 디렉토리에 실행을 자동화할 배치 파일을 작성합니다.
```cmd
@echo off
cd /d "C:\Users\infomax\Desktop\dev\duck\Reports"
set GEMINI_API_KEY=your-actual-api-key-here
"C:\Users\infomax\AppData\Local\Programs\Python\Python312\python.exe" src\main.py >> run_log.txt 2>&1
```

### 2단계: Windows 작업 스케줄러 등록
1. Windows 검색창에 `작업 스케줄러` (Task Scheduler)를 입력하고 실행합니다.
2. 우측 [작업] 패널에서 **[기본 작업 만들기...]**를 클릭합니다.
3. **이름 및 설명**을 입력합니다:
   - 이름: `금융 보고서 모니터링 에이전트`
   - 설명: `한국은행 및 KDI 최신 보고서 자동 요약 및 Outlook 초안 생성`
4. **트리거**를 선택합니다:
   - `매일` 선택 후 [다음] 클릭.
   - 원하는 시간(예: 오전 09:00:00)을 지정하고 [다음] 클릭.
5. **동작**을 선택합니다:
   - `프로그램 시작` 선택 후 [다음] 클릭.
6. **프로그램/스크립트** 설정:
   - [찾아보기]를 눌러 앞서 작성한 `run_agent.bat` 배치 파일을 지정합니다.
   - **시작 위치(옵션)**에 프로젝트 루트 절대 경로인 `C:\Users\infomax\Desktop\dev\duck\Reports`를 입력합니다.
7. [마침]을 클릭하여 작업을 완료합니다.
