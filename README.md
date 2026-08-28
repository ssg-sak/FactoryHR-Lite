# FactoryHR Lite

[Live Demo](https://factoryhr-frontend.onrender.com/) · [API `/health`](https://factoryhr-backend.onrender.com/health) · [Docs](https://factoryhr-backend.onrender.com/docs)

제조업 직원·근태 데이터를 관리하고 데이터 무결성 검증, 운영 KPI, PDF/CSV 보고서와 AI 보조 요약을 제공하는 풀스택 HR 운영 웹서비스입니다. 사내 시스템을 가정하여 관리되는 사용자 인증과 viewer/admin 역할 기반 권한을 적용했습니다.

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
| Backend pytest | **49 passed** in 27.16s |
| Frontend vitest | **10 passed** |
| Playwright smoke | **4 passed** (8.9s), Compose `http://127.0.0.1:3000`, `admin` / `admin-local` |
| lint / typecheck / build | passed (Next.js 15.5.24) |
| Alembic | `20260828_0003` (head), `alembic check` 통과 |
| PDF | Compose Docker 200, 141,032 bytes. 이전 Windows 로컬 200, 203,751 bytes. KPI 46 / 4 / 32.8 / 0.35 / 3.46 / 6.92 일치 |
| CSV | UTF-8 BOM, 직원·근태 실제 생성 |
| AI | 키 없음 → `503`. 이 Compose는 키 있어 200. 모델 `gemini-3.1-flash-lite` |
| GitHub Actions | 이 PR의 Actions 결과로 확인 |
| Docker Compose | 2026-08-28 재빌드 확인. db `5434:5432`, API 8000, web 3000. `/health` 200, admin/viewer 로그인, viewer 쓰기 403 |
| Authentication | Argon2 + JWT access. 공개 회원가입 없음. viewer/admin. `/signup` 없음 |
| Live Demo | [Web](https://factoryhr-frontend.onrender.com/) · [API `/health`](https://factoryhr-backend.onrender.com/health). 이 브랜치 인증은 merge·배포 후 확인 |

## 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [핵심 기능](#2-핵심-기능)
3. [시스템 아키텍처](#3-시스템-아키텍처)
4. [기술 스택](#4-기술-스택)
5. [DB 설계](#5-db-설계)
6. [프로젝트 구조](#6-프로젝트-구조)
7. [실행 방법](#7-실행-방법)
8. [API](#8-api)
9. [한계](#9-한계)
10. [개발 과정 / 트러블슈팅](#10-개발-과정--트러블슈팅)
11. [License](#11-license)
12. [Author](#12-author)

---

## 1. 프로젝트 소개

제조 현장에서는 직원 명단만으로 운영 현황을 보기 어렵습니다.
누가 어느 공장·생산라인·교대조에 있는지, 배치가 맞는지,
근태가 입사·퇴사 기간 안에 있는지를 같이 봐야 합니다.

| `/login` | 로그인. 공개 회원가입 없음 |
| `/dashboard` | 조회 조건, 데이터 검증 상태, 핵심 지표, 차트 |
| `/employees` | 직원 검색·필터. 쓰기는 admin |
| `/attendance` | 근태 조회. 쓰기는 admin |
| `/reports` | 미리보기, PDF/CSV, AI 요약 |

FactoryHR Lite는 사내 HR 운영 시스템을 가정하므로 공개 회원가입을 제공하지 않습니다. 사용자 계정은 관리되는 방식으로 발급되며 인증 후 역할에 따라 기능 접근 범위가 달라집니다.

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

### Authentication / Authorization

사내 HR 운영 시스템을 가정하여 self-signup을 의도적으로 제공하지 않습니다.
계정은 seed/bootstrap으로 발급합니다. 비밀번호는 Argon2, 세션은 JWT access token입니다.

| 기능 | viewer | admin |
|---|---|---|
| Dashboard 조회 | O | O |
| 직원 조회 | O | O |
| 직원 수정 | X | O |
| 근태 조회 | O | O |
| 근태 수정 | X | O |
| Report / PDF / CSV / AI | O | O |

Live Demo 조회 계정: `viewer` / `viewer-demo` (합성 데이터, 쓰기 API는 403).
JWT는 프론트 `localStorage`에 둡니다. Render 프론트/API가 호스트가 나뉘어 Authorization 헤더를 쓰기 위한 데모 선택이며, SSO/MFA가 아닙니다.

---

## 3. 시스템 아키텍처

```text
[PostgreSQL]
  Unique / Check / Trigger / 복합 FK
        ↓
[FastAPI]
  인증(JWT) · 직원·근태·마스터 · KPI · 정합성 건수 · PDF/CSV · AI(선택)
        ↓
[Next.js]  로그인 / 대시보드 / 직원 / 근태 / 리포트
        ╎  KPI JSON만
        ↓
[Gemini]
```

브라우저는 `NEXT_PUBLIC_API_URL`로 FastAPI를 호출합니다.
PDF·CSV는 백엔드가 파일로 내려줍니다.

---

## 4. 기술 스택

| 영역 | 기술 | 이 프로젝트에서의 역할 |
|---|---|---|
| **Frontend** | Next.js App Router, React, TypeScript, Tailwind | 대시보드·직원·근태·리포트 화면과 타입 기반 UI 구성 |
| **서버 상태 / Form** | TanStack Query, React Hook Form, Zod | API 조회·캐싱·갱신, 입력 폼 상태 관리와 사용자 입력 검증 |
| **Visualization** | Recharts | 인력 구성·근태·잔업 등 대시보드 지표 시각화 |
| **Backend** | Python, FastAPI, Pydantic, SQLAlchemy 2.x, psycopg, pwdlib(Argon2), PyJWT | REST API, 요청·응답 검증, JWT 인증, PostgreSQL 접근 |
| **Database** | PostgreSQL, Alembic | 직원·근태 데이터와 무결성 제약 저장, DB 스키마 변경 이력 관리 |
| **Report / AI** | ReportLab, Matplotlib, Gemini (`httpx`) | PDF 보고서·차트 생성, 계산된 KPI 기반 AI 보조 요약 호출 |
| **Test / DevOps** | Pytest, Vitest, Playwright(smoke), GitHub Actions, Docker Compose, Render Blueprint (`render.yaml`) | 백엔드·프론트·주요 사용자 흐름 검증, CI·개발환경·배포 설정 관리 |

서버 데이터는 TanStack Query, 페이지 UI는 `useState`,
대시보드·리포트가 공유하는 조회 조건만 Context입니다.

---

## 5. DB 설계

```text
departments          factories              users (인증, KPI와 독립)
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
| users | bootstrap admin + demo viewer |

정합성: `employee_number` UNIQUE, `(employee_id, work_date)` UNIQUE,
`(production_line_id, factory_id)` 복합 FK, 업무 FK `ON DELETE RESTRICT`,
근무 0~16 / 잔업 0~8 check, 입사 전·퇴사 후 근태는 trigger + API.

스키마 변경은 Alembic입니다. head: `20260828_0003` (`users`).

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

`.env.example`을 `.env`로 복사합니다. `GEMINI_API_KEY`와 `BOOTSTRAP_ADMIN_PASSWORD`는 비워 둘 수 있습니다.
키와 DB 비밀번호, `JWT_SECRET`은 Git에 넣지 않습니다.

Compose 기본값: demo viewer `viewer` / `viewer-demo`, 로컬 admin `admin` / `admin-local`. 이 값은 데모용이며 production secret이 아닙니다.

### Docker Compose

```powershell
Copy-Item .env.example .env
docker compose up --build
```

http://localhost:3000 · API http://localhost:8000 · `/docs`

호스트 5432가 이미 쓰이면 Compose DB는 `5434:5432`로 엽니다. 컨테이너 안에서는 그대로 `db:5432`입니다.

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

`npm run e2e`는 Compose 또는 로컬 서버가 떠 있을 때 Playwright smoke입니다. GitHub Actions에는 넣지 않았습니다.

```powershell
$env:E2E_BASE_URL='http://127.0.0.1:3000'
$env:E2E_USERNAME='admin'
$env:E2E_PASSWORD='admin-local'
npm run e2e
```

이 머신에서 Compose Postgres는 `5434`입니다. pytest는 예를 들어:

```powershell
$env:TEST_DATABASE_URL='postgresql+psycopg://factoryhr:factoryhr@127.0.0.1:5434/factoryhr_test'
```

### Render

[New Blueprint](https://dashboard.render.com/blueprint/new?repo=https://github.com/ssg-sak/FactoryHR-Lite)에서 GitHub 저장소를 연결하고 Apply 합니다.

`render.yaml`이 만드는 것:

| 리소스 | 이름 | 역할 |
|---|---|---|
| PostgreSQL | `factoryhr-db` | 무료, 16, 30일 만료 |
| Web | `factoryhr-backend` | migrate + seed 후 FastAPI, `/health` |
| Web | `factoryhr-frontend` | Next.js. API URL은 백엔드 공개 URL |

Apply 화면에서 `GEMINI_API_KEY`는 비워 두어도 됩니다. 넣으면 Reports에서 AI 요약이 동작합니다.
`BOOTSTRAP_ADMIN_PASSWORD`는 Dashboard에서 직접 넣습니다(`sync: false`). 넣지 않으면 admin 계정이 만들어지지 않습니다.
Demo viewer `viewer` / `viewer-demo`는 blueprint에 공개 데모 값으로 들어 있습니다.
`JWT_SECRET`은 Render가 생성합니다. production secret을 Git에 넣지 않습니다.

Live:

- Web: https://factoryhr-frontend.onrender.com/
- API: https://factoryhr-backend.onrender.com/
- Health: https://factoryhr-backend.onrender.com/health → `{"status":"ok","database":"connected"}`

이 README의 인증·RBAC는 `feat/auth-rbac-final` 기준입니다. Live 로그인·viewer 403은 merge 후 배포를 확인한 뒤에만 기입합니다.
무료 플랜은 cold start가 있습니다.

`DATABASE_URL`이 `postgres://`이면 `postgresql+psycopg://`로 바꿉니다. 프론트 공개 URL은 `FRONTEND_URL`로 CORS에 들어갑니다. Next.js는 Render `$PORT`를 사용합니다.

---

## 8. API

공통 집계 필터: `date_from`, `date_to`, `department_id`, `factory_id`, `production_line_id`, `shift_id`

| 구분 | Method | Endpoint |
|---|---|---|
| 인증 | POST | `/auth/login` |
| | GET | `/auth/me` |
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

공개: `GET /health`, `POST /auth/login`. 그 외 업무 API는 Bearer JWT. GET은 viewer/admin, 변경은 admin만.

확인: `/health` 200 `database: connected`, `/openapi.json` 200, `/docs` HTML 200.

---

## 9. 한계

- seed는 실제 HRIS가 아닌 고정 난수
- 출입기·ERP 연동 없음. 생산량·품질·임금 없음
- 조직/라인 과거 배치 이력 없음. 근태의 공장/라인/교대는 현재 배치
- historical headcount snapshot이 없어 turnover rate를 계산하지 않음
- 공개 self-signup 없음 — 사내 발급 구조를 따른 설계
- 실제 기업 SSO/MFA 수준의 인증 시스템은 아님
- AI는 KPI 보조 요약. 노무 판단용이 아님
- PDF 한글은 시스템 CJK 폰트(로컬: 맑은 고딕). Render 네이티브 인스턴스에는 CJK가 없어 Live PDF가 더 작음
- 장기 운영 SLA를 증명한 시스템이 아님

---

## 10. 개발 과정 / 트러블슈팅

**공개 가입.**  
문제: 불특정 사용자가 계정을 만들면 사내 HR 운영 가정과 맞지 않음.  
판단: self-signup을 넣지 않음.  
구현: bootstrap 계정 + JWT + viewer/admin.  
결과: 로그인만 있고 `/signup`은 없음.

**viewer / admin.**  
문제: 조회 데모와 운영 쓰기를 같은 권한으로 두면 Live에서 데이터가 바뀜.  
판단: 조회와 변경을 나눔.  
구현: GET은 인증 사용자, POST/PATCH/DELETE는 admin. UI도 동일.  
결과: viewer 쓰기 요청은 403.

**DB와 API 양쪽 검증.**  
문제: 화면만 막으면 HTTP로 우회됨.  
판단: 제약은 DB와 서비스에 둔다.  
구현: Unique/Check/Trigger/복합 FK + FastAPI 검증.  
결과: 입사 전 근태, 근태 있는 직원 삭제 등이 API와 DB에서 거절됨.

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
Live 502: `gemini-2.0-flash`가 2026-06-01 종료됨. 기본 모델을 `gemini-3.1-flash-lite`로 변경.

**회귀 테스트.**  
문제: 대시보드를 붙이며 기존 CRUD 계약을 깨기 쉬움.  
판단: 기존 pytest 23개는 계약을 유지.  
구현: summary 필드를 빼지 않고 필터와 `resigned_in_period`만 추가.  
결과: 전체 **49 passed**.

---

## 11. License

MIT. [LICENSE](./LICENSE)

## 12. Author

ssg-sak · [GitHub](https://github.com/ssg-sak) · [FactoryHR-Lite](https://github.com/ssg-sak/FactoryHR-Lite)
