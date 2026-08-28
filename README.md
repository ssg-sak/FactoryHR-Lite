# FactoryHR Lite

제조업 인력·근태 데이터를 관리하고,
운영 KPI와 리포트를 제공하는 풀스택 HR 운영 웹서비스

FactoryHR Lite는 제조업 현장의 직원, 부서, 공장, 생산라인,
교대조, 근태 데이터를 관리하고 인력운영 지표를 확인할 수 있도록 만든
풀스택 HR 데이터 프로젝트입니다.

제조업 현장에서는 직원 명단만으로 운영 현황을 보기 어렵습니다.
누가 어느 공장·생산라인·교대조에 있는지, 그 배치가 맞는지,
근태가 입사·퇴사 기간 안에 있는지까지 같이 봐야 합니다.

이 저장소는 아래 순서로 데이터를 다룹니다.

```text
직원 / 근태 입력
  → 검증
  → PostgreSQL
  → FastAPI
  → KPI 집계
  → Dashboard / PDF / CSV
  → Next.js
```

보기 좋은 대시보드보다, 먼저 신뢰할 수 있는 데이터를 만드는 것에 초점을 두었습니다.
임의 점수나 “위험도” 같은 설명 불가 지표는 만들지 않습니다.

---

## 1. 프로젝트 소개

화면은 네 개입니다.

| 경로 | 내용 |
|---|---|
| `/dashboard` | KPI, 필터, 차트, Data Quality |
| `/employees` | 직원 검색·필터·CRUD |
| `/attendance` | 근태 조회·CRUD |
| `/reports` | 리포트 미리보기, PDF/CSV, AI 요약 |

백엔드는 FastAPI, 데이터는 PostgreSQL, 스키마는 Alembic으로 관리합니다.
로그인 기능은 없습니다.

---

## 2. 핵심 기능

### 2-1. 직원 관리

- 등록, 목록, 상세, 수정, 삭제
- 이름 검색
- 부서 / 공장 / 생산라인 / 교대조 / 재직상태 필터
- 페이지네이션

공장을 바꾸면 해당 공장의 생산라인만 선택할 수 있습니다.
공장과 생산라인이 서로 다른 공장이면 API `400`, DB 복합 FK로도 막습니다.

재직(`active`)은 퇴사일이 없어야 하고, 퇴사(`resigned`)는 퇴사일이 있어야 합니다.
퇴사일이 입사일보다 빠르면 거절합니다.

근태가 남아 있는 직원은 삭제하지 않습니다. `DELETE`는 `409 Conflict`입니다.

### 2-2. 근태 관리

- 등록, 수정, 삭제
- 기간 / 직원 / 근태상태 필터
- 근무시간, 잔업시간
- 상태: 정상(`present`), 지각(`late`), 결근(`absent`), 휴가(`leave`)

서버와 DB에서 같이 막는 규칙:

- 입사 전 날짜
- 퇴사 후 날짜
- 근무시간 0 미만 또는 16 초과
- 잔업시간 0 미만 또는 8 초과
- 같은 직원 + 같은 날짜 중복

입사일·퇴사일을 나중에 바꿔도, 이미 있는 근태와 어긋나면 `409`입니다.

### 2-3. HR Dashboard

필터: `date_from`, `date_to`, 부서, 공장, 생산라인, 교대조.
공장을 바꾸면 생산라인 옵션이 바뀝니다.

KPI (코드의 정의와 동일):

| 지표 | 정의 |
|---|---|
| 현재 재직 인원 | `status=active` 직원 수 |
| 기간 내 퇴사 인원 | `status=resigned` 이고 `resigned_at`이 선택 기간에 포함된 인원 |
| 평균 근속개월 | 근속일 / 30.4375. 재직은 report date − `hired_at`, 퇴사는 `resigned_at` − `hired_at`. report date는 `date_to` 또는 `CURRENT_DATE` |
| 평균 잔업시간 | 선택 기간 `attendance.overtime_hours` 평균 |
| 결근 기록 비율 | 선택 기간 attendance 중 `absent` 비율(%) |
| 지각 기록 비율 | 선택 기간 attendance 중 `late` 비율(%) |

차트:

- 공장별 재직 인원 (가로 막대)
- 생산라인별 재직 인원 (가로 막대)
- 교대조별 재직 인원 (막대)
- 날짜별 결근/지각 비율 (선)
- 생산라인별 평균 잔업 (막대)
- 교대조별 평균 잔업 (막대)
- 근속 구간 분포: 0~6개월 / 6~12개월 / 1~3년 / 3년 이상 (재직만)
- 부서별 기간 내 퇴사 인원 (막대)

재직 인원 차트는 현재 `status=active` 기준입니다. 과거 배치 이력은 없습니다.
퇴사는 인원 수로만 보여 줍니다. 평균 재직 분모가 없어 turnover rate는 계산하지 않습니다.

각 KPI 카드에 정의를 같이 표시합니다.

### 2-4. Data Quality

대시보드 하단과 리포트에서 검사 결과를 건수 그대로 보여 줍니다.
점수는 만들지 않습니다. unique/check가 있어서 0이어야 하는 항목도 조회합니다.

- 전체 직원 수, 전체 근태 건수
- `employee_number` 중복
- 직원+날짜 근태 중복
- 근무시간 범위 위반
- 잔업시간 범위 위반
- 입사 전 근태
- 퇴사 후 근태
- 공장-생산라인 불일치

### 2-5. PDF / CSV Report

`/reports`에서 필터를 건 뒤 다운로드합니다. 생성은 FastAPI가 합니다.

- `GET /api/reports/workforce.pdf`
- `GET /api/reports/employees.csv`
- `GET /api/reports/attendance.csv`

PDF 구성:

1. 표지 (기간, 생성 시각, 적용 필터)
2. Executive Summary
3. Workforce Structure
4. Attendance & Overtime
5. Tenure / 기간 내 퇴사
6. Data Quality
7. Metric Definitions & Limitations

한글은 실행 환경의 Noto Sans CJK 또는 맑은 고딕을 찾습니다.
폰트가 없으면 경고를 넣고 Helvetica로 만듭니다. 깨진 한글 PDF를 조용히 내려주지는 않습니다.

CSV는 UTF-8 BOM을 붙여 Excel에서 한글이 깨지지 않게 했습니다.

### 2-6. AI HR Summary

`POST /api/reports/ai-summary`는 Gemini에 직원 원문을 보내지 않습니다.
FastAPI가 계산한 KPI JSON만 전달합니다.

응답:

```json
{
  "observations": [],
  "additional_data_needed": [],
  "cannot_conclude": []
}
```

규칙: 제공된 KPI 밖의 사실을 만들지 않음, 원인을 단정하지 않음, 상관을 인과로 쓰지 않음,
직원을 개인적으로 평가하지 않음, 해고/채용을 추천하지 않음.

`GEMINI_API_KEY`가 없으면 이 API만 `503`이고, 나머지 화면·PDF·CSV는 그대로 동작합니다.

---

## 3. 시스템 아키텍처

```text
[PostgreSQL]
      ↓
[SQLAlchemy + Check / Unique / Trigger]
      ↓
[FastAPI REST API]
      ├─ Employees / Attendance / Master Data
      ├─ Dashboard 집계
      ├─ Data Quality 조회
      └─ PDF / CSV / AI Summary
            ↓
      [Next.js]
      ├─ Dashboard
      ├─ Employees
      ├─ Attendance
      └─ Reports
            ╎
            ╎  (선택) 구조화 KPI JSON
            ↓
      [Gemini API]
```

브라우저는 `NEXT_PUBLIC_API_URL`로 FastAPI를 호출합니다.
PDF와 CSV 파일은 백엔드에서 만들어 첨부 다운로드합니다.

---

## 4. 기술 스택

### Frontend

- Next.js (App Router), React, TypeScript
- Tailwind CSS
- TanStack Query
- React Hook Form, Zod
- Recharts, Lucide React
- Vitest, React Testing Library

### Backend

- Python, FastAPI, Pydantic
- SQLAlchemy 2.x, psycopg

### Database

- PostgreSQL
- Alembic

### Reporting / AI

- ReportLab, Matplotlib
- Gemini API (`httpx`)

### Testing / DevOps

- Pytest (PostgreSQL 통합 테스트)
- GitHub Actions
- Docker Compose

---

## 5. DB 설계

테이블 6개입니다.

```text
departments          factories
      │                  │
      │                  ├── production_lines
      │                  │
      └──────── employees ──────── shifts
                    │
                    └── attendance
```

| 관계 | 설명 |
|---|---|
| departments 1:N employees | 부서 |
| factories 1:N production_lines | 공장별 라인 |
| factories 1:N employees | 직원 공장 |
| production_lines 1:N employees | 직원 라인 (nullable) |
| shifts 1:N employees | 교대조 |
| employees 1:N attendance | 근태 |

정합성:

- `employee_number` UNIQUE
- `(employee_id, work_date)` UNIQUE
- 직원 `(production_line_id, factory_id)` → `production_lines(id, factory_id)` 복합 FK
- 업무 FK는 모두 `ON DELETE RESTRICT`
- 직원 삭제가 근태를 cascade로 지우지 않음
- 근무시간 0~16, 잔업 0~8 check
- 입사 전/퇴사 후 근태는 PostgreSQL trigger와 API가 같이 차단

스키마 변경은 `Base.metadata.create_all()`이 아니라 Alembic migration입니다.
현재 head: `20260828_0002`.

---

## 6. 프로젝트 구조

```text
.
├── frontend/
│   ├── app/                 # dashboard, employees, attendance, reports
│   ├── components/
│   ├── lib/                 # API client, types
│   └── tests/
├── backend/
│   ├── app/
│   │   ├── core/            # settings, DB session
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── query.py         # 리포트/대시보드 공통 필터
│   │   └── main.py
│   ├── alembic/
│   ├── scripts/seed.py
│   └── tests/
├── .github/workflows/ci.yml
├── docker-compose.yml
├── .env.example
├── LICENSE
└── README.md
```

| 위치 | 역할 |
|---|---|
| `backend/app/services/` | 교차 테이블 검증, KPI 정의, PDF/CSV/AI |
| `backend/alembic/versions/` | 테이블·제약·trigger |
| `frontend/lib/api.ts` | FastAPI 호출 한곳 |
| `frontend/lib/errors.ts` | 400/409/422 메시지 |

---

## 7. 실행 방법

`.env.example`을 복사해 `.env`를 만듭니다. `GEMINI_API_KEY`는 비워 두어도 됩니다.
실제 키는 Git에 넣지 않습니다.

### A. Docker Compose

Docker CLI가 있는 환경:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

- 화면: http://localhost:3000
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

backend 컨테이너는 DB healthy 이후 기동하고, 시작 시 `alembic upgrade head`와 seed를 실행합니다.
직원 데이터가 있으면 seed는 건너뜁니다.

이 저장소를 작업한 Windows 환경에는 Docker CLI가 없어 compose 기동은 여기서 확인하지 못했습니다.

### B. Local Development

PostgreSQL이 `DATABASE_URL`에 연결 가능한 상태에서:

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt

docker compose up -d db

Set-Location backend
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload
```

다른 터미널:

```powershell
Set-Location frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Seed (빈 직원 테이블 기준): 부서 4, 공장 2, 생산라인 6, 교대조 2, 직원 50, 평일 근태 1,070건.
기간은 2026-07-29 ~ 2026-08-27, 난수 시드 `20260828`.

### 테스트 / 검증

백엔드는 SQLite를 쓰지 않습니다. DB 이름이 `_test`로 끝나는 PostgreSQL만 허용합니다.

```powershell
docker compose exec db createdb -U factoryhr factoryhr_test
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
```

실행해서 확인한 결과:

| 항목 | 결과 |
|---|---|
| Backend pytest | **35 passed** (기존 23 + 대시보드/리포트 12) |
| Frontend vitest | **7 passed** |
| Frontend lint | passed |
| Frontend typecheck | passed |
| Frontend build | passed (Next.js 15.5.24) |
| Alembic | `20260828_0002` (head) |
| Seed | 직원 50, 근태 1,070 |
| GitHub Actions | `.github/workflows/ci.yml` 작성. remote CI 실행 여부는 이 README에 적지 않음 |
| Docker Compose up | 미실행 (Docker CLI 없음) |

---

## 8. API 목록

공통 대시보드/리포트 필터: `date_from`, `date_to`, `department_id`, `factory_id`, `production_line_id`, `shift_id`

### Employees

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/employees` | 목록. `page`, `page_size`, `name`, `department_id`, `factory_id`, `production_line_id`, `shift_id`, `status` |
| POST | `/api/employees` | 등록 |
| GET | `/api/employees/{id}` | 상세 |
| PATCH | `/api/employees/{id}` | 부분 수정 |
| DELETE | `/api/employees/{id}` | 근태 없을 때만 삭제 |

### Attendance

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/attendance` | 목록. `employee_id`, `date_from`, `date_to`, `attendance_status` |
| POST | `/api/attendance` | 등록 |
| GET | `/api/attendance/{id}` | 상세 |
| PATCH | `/api/attendance/{id}` | 부분 수정 |
| DELETE | `/api/attendance/{id}` | 삭제 |

### Master Data

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/departments` | 부서 |
| GET | `/api/factories` | 공장 |
| GET | `/api/production-lines` | 생산라인. `factory_id`로 필터 |
| GET | `/api/shifts` | 교대조 |

### Dashboard

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/dashboard/summary` | KPI. 기존 필드 유지, `resigned_in_period` 등 추가 |
| GET | `/api/dashboard/workforce-distribution` | 재직 분포, 기간 내 퇴사 |
| GET | `/api/dashboard/attendance-trend` | 날짜별 근태 비율 |
| GET | `/api/dashboard/overtime` | 라인/교대 평균 잔업 |
| GET | `/api/dashboard/tenure-distribution` | 재직 근속 밴드 |
| GET | `/api/dashboard/data-quality` | 정합성 건수 |

### Reports

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/reports/workforce.pdf` | PDF 첨부 |
| GET | `/api/reports/employees.csv` | 직원 CSV |
| GET | `/api/reports/attendance.csv` | 근태 CSV |
| POST | `/api/reports/ai-summary` | KPI 기반 요약. 키 없으면 503 |

### System

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/health` | 앱·DB 연결 |
| GET | `/docs` | Swagger |
| GET | `/openapi.json` | OpenAPI |

---

## 9. 프로젝트 한계 및 향후 개선

한계:

- seed는 실제 기업 HRIS가 아닌 고정 난수 데이터
- 근태는 출입기/ERP 연동이 아님
- 생산량, 품질, 임금 없음
- 직원 배치 이력이 없음. 근태의 공장/라인/교대는 현재 배치
- 로그인·권한이 없음. 네트워크에 올리면 누구나 API를 호출할 수 있음
- 근태/퇴사 숫자로 원인을 단정할 수 없음
- AI는 계산된 KPI의 보조 요약
- 법률/노무 판단용이 아님
- PDF 한글은 시스템 CJK 폰트에 의존

이후 손볼 수 있는 방향:

- 배치 변경 이력
- Admin / Viewer 인증
- HRIS/ERP 연동
- 생산량 데이터와 조인
- 배포 환경
- Playwright 등 E2E

---

## 10. 개발 과정에서 배운 점 / 트러블슈팅

**직원 삭제와 근태.**  
처음에는 직원만 지우고 근태는 남기면 FK 때문에 막히거나, cascade로 같이 지워질 수 있었습니다.
운영 데이터를 실수로 지우는 쪽이 더 위험하다고 보고, FK는 `RESTRICT`, API는 근태가 있으면 `409`로 막았습니다.
근태를 먼저 정리한 뒤에만 직원을 지울 수 있습니다.

**공장과 생산라인.**  
라인 ID만 저장하면 다른 공장 라인을 고를 수 있습니다.
`(production_line_id, factory_id)` 복합 FK를 넣고, 서비스에서도 라인의 `factory_id`를 한 번 더 확인합니다.
테스트는 API `400`과 DB `IntegrityError`를 둘 다 봅니다.

**입사일/퇴사일 수정.**  
날짜 형식만 검사하면, 이미 있는 근태가 새 입사일보다 이전이 될 수 있습니다.
수정 전에 해당 직원의 최소/최대 `work_date`를 보고, 충돌하면 `409`를 냅니다.
근태 쪽 trigger만으로는 “직원 날짜를 줄이는 경우”를 설명하기 어렵습니다.

**Data Quality 점수.**  
99점 같은 값은 분모와 가중치를 설명하기 어렵습니다.
그래서 검사 항목별 건수만 보여 주기로 했습니다.
제약이 잘 동작하면 위반 건수는 0이고, 그것도 조회 결과입니다.

**퇴사율.**  
turnover rate는 보통 기간 평균 재직 인원이 분모입니다.
이 스키마에는 일별 재직 스냅샷이 없어서 분모를 정확히 못 만듭니다.
그래서 기간 내 퇴사 인원만 집계합니다.

**AI 입력.**  
테이블 dump를 모델에 넣으면 없는 사실을 만들기 쉽습니다.
집계 JSON만 보내고, `cannot_conclude`을 응답에 필수로 두었습니다.
키가 없을 때는 앱 전체가 죽지 않고 해당 버튼만 실패합니다.

**기존 테스트.**  
직원/근태 CRUD pytest 23개는 계약을 바꾸지 않는 기준으로 두었습니다.
대시보드 summary는 필드를 빼지 않고 필터와 `resigned_in_period`만 추가했습니다.
그 위에 집계·PDF·CSV·AI 테스트를 더해 현재 35개가 통과합니다.

---

## 11. License

This project is licensed under the MIT License.

[LICENSE](./LICENSE)

---

## 12. Author

ssg-sak

- GitHub: [ssg-sak](https://github.com/ssg-sak)
- Repository: [FactoryHR-Lite](https://github.com/ssg-sak/FactoryHR-Lite)
