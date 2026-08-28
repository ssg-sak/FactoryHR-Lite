# FactoryHR Lite

제조업 직원·근태 데이터를 관리하고
데이터 검증, 운영 KPI, PDF/CSV 리포트,
AI 보조 요약을 제공하는 풀스택 HR 운영 웹서비스.

```text
Employee / Attendance
  → Validation
  → PostgreSQL
  → FastAPI
  → Dashboard / Report
  → Next.js
```

보기 좋은 화면보다, 먼저 믿을 수 있는 데이터를 만드는 것에 초점을 두었습니다.
임의 점수나 turnover rate처럼 분모를 설명할 수 없는 지표는 두지 않습니다.

![대시보드](docs/images/dashboard.png)

| | 검증된 값 |
|---|---|
| Seed | 직원 **50**, 근태 **1,070** (2026-07-29 ~ 2026-08-27) |
| Backend pytest | **35 passed** in 11.35s |
| Frontend vitest | **7 passed** |
| Playwright smoke | **4 passed** in 12.4s |
| lint / typecheck / build | passed (Next.js 15.5.24) |
| Alembic | `20260828_0002` (head), `alembic check` 통과 |
| PDF | 200, `application/pdf`, 203,751 bytes, KPI 46 / 4 / 32.8 / 0.35 / 3.46 / 6.92 일치 |
| CSV | UTF-8 BOM, 직원·근태 실제 생성 |
| AI | `GEMINI_API_KEY` 없음 → `503`, PDF/CSV/화면은 정상 |
| GitHub Actions | **passed** (main push, backend + frontend) |
| Docker Compose | 이 환경에 Docker CLI 없음. **미실행** |
| Live Demo | Blueprint 준비됨. Render Apply 후 URL 기입 |

## 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [핵심 기능](#2-핵심-기능)
3. [시스템 아키텍처](#3-시스템-아키텍처)
4. [기술 스택](#4-기술-스택)
5. [DB 설계](#5-db-설계)
6. [프로젝트 구조](#6-프로젝트-구조)
7. [실행 방법](#7-실행-방법)
8. [API](#8-api)
9. [한계 및 향후 개선](#9-한계-및-향후-개선)
10. [개발 과정 / 트러블슈팅](#10-개발-과정--트러블슈팅)
11. [License](#11-license)
12. [Author](#12-author)

---

## 1. 프로젝트 소개

제조 현장에서는 직원 명단만으로 운영 현황을 보기 어렵습니다.
누가 어느 공장·생산라인·교대조에 있는지, 배치가 맞는지,
근태가 입사·퇴사 기간 안에 있는지를 같이 봐야 합니다.

화면 네 개:

| 경로 | 내용 |
|---|---|
| `/dashboard` | 조회 조건, 데이터 검증 상태, 핵심 지표, 차트 |
| `/employees` | 직원 검색·필터·CRUD |
| `/attendance` | 근태 조회·CRUD |
| `/reports` | 미리보기, PDF/CSV, AI 요약 |

로그인은 없습니다. 네트워크에 올리면 API가 열려 있습니다.

![직원 관리](docs/images/employees.png)

---

## 2. 핵심 기능

### 직원 / 근태

- 직원 등록·수정·삭제, 이름 검색, 조직·재직상태 필터, 페이지네이션
- 공장을 바꾸면 그 공장의 생산라인만 선택 가능
- 재직은 퇴사일 없음, 퇴사는 퇴사일 필수
- 근태가 있는 직원은 삭제하지 않음 (`409`)
- 근태 상태: 정상 / 지각 / 결근 / 휴가
- 입사 전·퇴사 후 날짜, 근무 0~16시간, 잔업 0~8시간, 직원+날짜 중복은 API와 DB가 같이 차단

### 지표

조회 조건: `date_from`, `date_to`, 부서, 공장, 생산라인, 교대조.
대시보드와 리포트는 같은 필터 상태와 `workforceQuery` 직렬화를 씁니다.

화면의 기본 문구는 사람용이고, ⓘ에 계산식을 둡니다.

| 지표 | 계산 (코드 기준) |
|---|---|
| 현재 재직 인원 | `status=active` 직원 수 |
| 선택 기간 퇴사 인원 | `status=resigned` 이고 `resigned_at`이 선택 기간에 포함 |
| 평균 근속개월 | 근속일 / 30.4375. 재직: report date − `hired_at`, 퇴사: `resigned_at` − `hired_at` |
| 평균 잔업시간 | 선택 기간 `attendance.overtime_hours` 산술평균 |
| 결근 기록 비율 | 선택 기간 attendance 중 `absent` 비율(%) |
| 지각 기록 비율 | 선택 기간 attendance 중 `late` 비율(%) |

재직 차트는 현재 배치만 집계합니다. 과거 라인 이력은 없습니다.
turnover rate는 일별 재직 스냅샷이 없어 계산하지 않습니다.

seed 기간 전체 조회에서 확인한 값: 재직 46, 기간 내 퇴사 4, 평균 근속 32.8개월, 평균 잔업 0.35시간, 결근 3.46%, 지각 6.92%.

### Data Quality

점수를 만들지 않습니다. 실제 조회 결과: **7개 항목 확인 · 위반 0건**.

중복 사번, 직원/날짜 중복 근태, 비정상 근무·잔업, 입사 전 근태, 퇴사 후 근태, 공장-라인 불일치.

### 리포트 / AI

![리포트](docs/images/reports.png)

- PDF: 표지 → 핵심 지표 → 인력 구성 → 근태·잔업 → 근속·퇴사 → 정합성 → 정의와 한계
- CSV: UTF-8 BOM
- AI: 계산된 KPI JSON만 Gemini에 전달. 키 없으면 이 API만 `503`

---

## 3. 시스템 아키텍처

```text
[PostgreSQL]
  Unique / Check / Trigger / 복합 FK
        ↓
[FastAPI]
  직원·근태·마스터 · KPI · 정합성 건수 · PDF/CSV · AI(선택)
        ↓
[Next.js]  대시보드 / 직원 / 근태 / 리포트
        ╎  KPI JSON만
        ↓
[Gemini]
```

브라우저는 `NEXT_PUBLIC_API_URL`로 FastAPI를 호출합니다.
PDF·CSV는 백엔드가 파일로 내려줍니다.

---

## 4. 기술 스택

**Frontend:** Next.js App Router, React, TypeScript, Tailwind, TanStack Query, React Hook Form, Zod, Recharts  
**Backend:** Python, FastAPI, Pydantic, SQLAlchemy 2.x, psycopg  
**Database:** PostgreSQL, Alembic  
**Report / AI:** ReportLab, Matplotlib, Gemini (`httpx`)  
**Test / DevOps:** Pytest, Vitest, Playwright(smoke), GitHub Actions, Docker Compose, Render Blueprint(`render.yaml`)

서버 데이터는 TanStack Query, 페이지 UI는 `useState`,
대시보드·리포트가 공유하는 조회 조건만 Context입니다.

---

## 5. DB 설계

```text
departments          factories
      │                  │
      │                  ├── production_lines
      │                  │
      └──────── employees ──────── shifts
                    │
                    └── attendance
```

실제 조회:

| 테이블 | rows |
|---|---|
| departments | 4 |
| factories | 2 |
| production_lines | 6 |
| shifts | 2 |
| employees | 50 |
| attendance | 1,070 |

정합성: `employee_number` UNIQUE, `(employee_id, work_date)` UNIQUE,
`(production_line_id, factory_id)` 복합 FK, 업무 FK `ON DELETE RESTRICT`,
근무 0~16 / 잔업 0~8 check, 입사 전·퇴사 후 근태는 trigger + API.

스키마 변경은 Alembic입니다. head: `20260828_0002`.

---

## 6. 프로젝트 구조

```text
.
├── frontend/          app, components, lib/api.ts, tests, e2e
├── backend/
│   ├── app/           models, routers, services, query.py
│   ├── alembic/
│   ├── scripts/seed.py
│   └── tests/
├── docs/images/       실제 화면 스크린샷
├── .github/workflows/ci.yml
├── docker-compose.yml
├── render.yaml
├── .env.example
├── LICENSE
└── README.md
```

---

## 7. 실행 방법

`.env.example`을 `.env`로 복사합니다. `GEMINI_API_KEY`는 비워 두어도 됩니다.
키와 DB 비밀번호는 Git에 넣지 않습니다.

### Docker Compose

```powershell
Copy-Item .env.example .env
docker compose up --build
```

http://localhost:3000 · API http://localhost:8000 · `/docs`

이 Windows 작업 환경에는 Docker CLI가 없어 compose 기동은 **실행하지 못했습니다**.

### 로컬

PostgreSQL이 `DATABASE_URL`에 붙는 상태에서:

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Set-Location backend
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload
```

```powershell
Set-Location frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

### 테스트

백엔드는 SQLite를 쓰지 않습니다. DB 이름이 `_test`로 끝나는 PostgreSQL만 허용합니다.

```powershell
Set-Location backend
$env:TEST_DATABASE_URL='postgresql+psycopg://factoryhr:factoryhr@localhost:5432/factoryhr_test'
python -m pytest -q
```

```powershell
Set-Location frontend
npm run lint
npm run typecheck
npm test
npm run build
npm run e2e
```

`npm run e2e`는 로컬에서 `http://localhost:3000`과 API가 떠 있을 때 Playwright smoke입니다. GitHub Actions에는 넣지 않았습니다.

### Render

[New Blueprint](https://dashboard.render.com/blueprint/new?repo=https://github.com/ssg-sak/FactoryHR-Lite)에서 GitHub 저장소를 연결하고 Apply 합니다.

`render.yaml`이 만드는 것:

| 리소스 | 이름 | 역할 |
|---|---|---|
| PostgreSQL | `factoryhr-db` | 무료, 16, 30일 만료 |
| Web | `factoryhr-backend` | migrate + seed 후 FastAPI, `/health` |
| Web | `factoryhr-frontend` | Next.js. API URL은 백엔드 공개 URL |

Apply 화면에서 `GEMINI_API_KEY`는 비워 두어도 됩니다. 넣으면 Reports에서 AI 요약이 동작합니다.

배포 후 확인할 것:

1. `https://<backend>.onrender.com/health` → `{"status":"ok","database":"connected"}`
2. 프론트에서 `/dashboard` `/employees` `/attendance` `/reports` 한 번씩
3. 첫 요청은 무료 플랜 cold start로 1~2분 걸릴 수 있음

`DATABASE_URL`이 `postgres://`이면 `postgresql+psycopg://`로 바꿉니다. 프론트 공개 URL은 `FRONTEND_URL`로 CORS에 들어갑니다. Next.js는 Render `$PORT`를 사용합니다.

Live Demo URL은 Apply가 끝난 뒤 이 README 표에 기입합니다.

---

## 8. API

공통 집계 필터: `date_from`, `date_to`, `department_id`, `factory_id`, `production_line_id`, `shift_id`

| 구분 | Method | Endpoint |
|---|---|---|
| 직원 | GET/POST | `/api/employees` |
| | GET/PATCH/DELETE | `/api/employees/{id}` |
| 근태 | GET/POST | `/api/attendance` |
| | GET/PATCH/DELETE | `/api/attendance/{id}` |
| 마스터 | GET | `/api/departments` `/api/factories` `/api/production-lines` `/api/shifts` |
| 집계 | GET | `/api/dashboard/summary` |
| | GET | `/api/dashboard/workforce-distribution` |
| | GET | `/api/dashboard/attendance-trend` |
| | GET | `/api/dashboard/overtime` |
| | GET | `/api/dashboard/tenure-distribution` |
| | GET | `/api/dashboard/data-quality` |
| 리포트 | GET | `/api/reports/workforce.pdf` |
| | GET | `/api/reports/employees.csv` |
| | GET | `/api/reports/attendance.csv` |
| | POST | `/api/reports/ai-summary` |
| 시스템 | GET | `/health` `/docs` `/openapi.json` |

확인: `/health` 200 `database: connected`, `/openapi.json` 200, `/docs` HTML 200.

---

## 9. 한계 및 향후 개선

- seed는 실제 HRIS가 아닌 고정 난수
- 출입기·ERP 연동 없음. 생산량·품질·임금 없음
- 배치 이력 없음. 근태의 공장/라인/교대는 현재 배치
- 인증 없음
- AI는 KPI 보조 요약. 노무 판단용이 아님
- PDF 한글은 시스템 CJK 폰트(이 환경: 맑은 고딕)
- Docker Compose는 이 Windows 환경에 CLI가 없어 미실행
- Render live URL은 Blueprint Apply 후 기입

이후: 배치 이력, Admin/Viewer, HRIS 연동, 배포 환경 E2E.

---

## 10. 개발 과정 / 트러블슈팅

**직원 삭제.**  
문제: cascade면 근태가 같이 지워질 수 있음.  
판단: 운영 데이터 손실이 더 위험함.  
구현: FK `RESTRICT`, 근태 있으면 API `409`.  
결과: Playwright에서 삭제 시도 시 “근태 기록이 있는 직원은 삭제할 수 없습니다.”

**공장-라인.**  
문제: 라인 ID만 두면 다른 공장 라인을 고를 수 있음.  
판단: API만으로는 부족함.  
구현: 복합 FK + 서비스 검증. 테스트는 `400`과 `IntegrityError`.  
결과: 공장 변경 시 생산라인 필터가 비워지고 해당 공장 라인만 재조회됨.

**입사일/퇴사일 수정.**  
문제: 날짜 형식만 보면 기존 근태가 새 입사일 이전이 됨.  
판단: trigger만으로는 직원 날짜를 줄이는 경우를 설명하기 어려움.  
구현: 수정 전 최소/최대 `work_date` 확인, 충돌 시 `409`.  
결과: 기존 근태를 깨는 입사일 축소가 거절됨.

**Data Quality 점수.**  
문제: 99점은 분모와 가중치를 설명하기 어려움.  
판단: 점수를 만들지 않음.  
구현: 항목별 건수 조회. 제약이 막으면 0이고, 그것도 조회 결과.  
결과: 실제 DB 기준 위반 0건.

**퇴사율.**  
문제: turnover의 분모는 보통 기간 평균 재직.  
판단: 일별 스냅샷이 없음.  
구현: 기간 내 퇴사 인원만 집계.  
결과: PDF에도 turnover rate를 쓰지 않음.

**AI 입력.**  
문제: 테이블 dump는 없는 사실을 만들기 쉬움.  
판단: 집계 JSON만 보냄.  
구현: `cannot_conclude` 필수, 키 없으면 해당 API만 `503`.  
결과: 키 없는 환경에서 PDF/CSV/대시보드는 그대로 동작.

**회귀 테스트.**  
문제: 대시보드를 붙이며 기존 CRUD 계약을 깨기 쉬움.  
판단: 기존 pytest 23개는 계약을 유지.  
구현: summary 필드를 빼지 않고 필터와 `resigned_in_period`만 추가.  
결과: 전체 **35 passed**.

---

## 11. License

MIT. [LICENSE](./LICENSE)

## 12. Author

ssg-sak · [GitHub](https://github.com/ssg-sak) · [FactoryHR-Lite](https://github.com/ssg-sak/FactoryHR-Lite)
