# FactoryHR Lite

제조 현장의 직원·공장·생산라인·교대조·근태를 한곳에서 보고,
**검증된 숫자**로 인력운영 지표와 리포트를 만드는 풀스택 웹서비스입니다.

직원 명단만 있으면 운영 현황이 보이지 않습니다.
누가 어느 공장·라인·교대조에 있는지, 그 배치가 맞는지,
근태가 입사·퇴사 기간 안에 있는지를 같이 봐야 합니다.

임의 점수나 “위험도” 같은 설명 불가 지표는 두지 않습니다.

```text
직원 / 근태 입력  →  검증  →  PostgreSQL  →  FastAPI KPI  →  Dashboard / PDF / CSV
                                                              ↳ (선택) KPI JSON → Gemini
```

[화면](http://localhost:3000) · [API docs](http://localhost:8000/docs) · [저장소](https://github.com/ssg-sak/FactoryHR-Lite)

## 목차

- [한눈에 보기](#한눈에-보기)
- [화면](#화면)
- [검증 → 지표 → 리포트](#검증--지표--리포트)
- [지표 정의](#지표-정의)
- [정합성](#정합성)
- [리포트와 AI](#리포트와-ai)
- [스키마와 코드 구조](#스키마와-코드-구조)
- [실행](#실행)
- [API](#api)
- [한계](#한계)
- [구현 메모](#구현-메모)
- [License](#license) · [Author](#author)

---

## 한눈에 보기

| | |
|---|---|
| 대상 | 제조업 인력운영 (로그인 없음) |
| 화면 | 대시보드 · 직원 관리 · 근태 관리 · 리포트 |
| 데이터 | PostgreSQL 6테이블, Alembic `20260828_0002` |
| 백엔드 | FastAPI, SQLAlchemy 2.x |
| 프론트 | Next.js App Router, TypeScript, Tailwind |
| 리포트 | PDF / CSV는 서버 생성. AI는 KPI JSON만 전달 |
| seed | 직원 50, 평일 근태 1,070 (2026-07-29 ~ 2026-08-27) |

프론트: Next.js, React, TanStack Query, React Hook Form, Zod, Recharts  
백엔드: Python, FastAPI, Pydantic, SQLAlchemy, psycopg, ReportLab, Matplotlib, Gemini(`httpx`)  
검증: Pytest 35, Vitest 7, GitHub Actions, Docker Compose

---

## 화면

| 경로 | 하는 일 |
|---|---|
| `/dashboard` | 조회 조건, 데이터 검증 상태, 핵심 지표, 차트 |
| `/employees` | 검색·필터·등록/수정/삭제, 상세 |
| `/attendance` | 기간·직원·상태 조회, 근태 CRUD |
| `/reports` | 같은 지표 미리보기, PDF/CSV, AI 요약 |

직원 화면에서 공장을 바꾸면 그 공장의 생산라인만 고를 수 있습니다.
재직은 퇴사일이 없어야 하고, 퇴사는 퇴사일이 있어야 합니다.
근태가 남아 있는 직원은 삭제하지 않습니다 (`409`).

근태 상태: 정상(`present`) · 지각(`late`) · 결근(`absent`) · 휴가(`leave`).
입사 전·퇴사 후 날짜, 근무 0~16시간, 잔업 0~8시간, 같은 직원+날짜 중복은 API와 DB가 같이 막습니다.

---

## 검증 → 지표 → 리포트

```text
[PostgreSQL]
  Check / Unique / Trigger / 복합 FK
        ↓
[FastAPI]
  직원·근태·마스터    집계 KPI    정합성 건수    PDF·CSV    AI(선택)
        ↓
[Next.js]  대시보드 / 직원 / 근태 / 리포트
        ╎
        ╎  구조화 KPI JSON만
        ↓
[Gemini]
```

브라우저는 `NEXT_PUBLIC_API_URL`로 FastAPI를 부릅니다.
PDF·CSV 파일은 백엔드가 만들어 첨부 다운로드합니다.
로그인이 없으므로, 네트워크에 올리면 API가 열려 있습니다.

---

## 지표 정의

조회 조건: `date_from`, `date_to`, 부서, 공장, 생산라인, 교대조.
화면의 기본 문구는 사람용이고, 카드의 **지표 정의**에 아래 계산식을 둡니다.

| 지표 | 계산 |
|---|---|
| 현재 재직 인원 | `status = active`인 직원 수 |
| 선택 기간 퇴사 인원 | `status = resigned`이고 `resigned_at`이 `[date_from, date_to]`에 포함 |
| 평균 잔업시간 | 선택 기간 `attendance.overtime_hours`의 산술평균 |
| 결근 기록 비율 | `absent` row 수 / 선택 기간 attendance row 수 × 100 |
| 지각 기록 비율 | `late` row 수 / 선택 기간 attendance row 수 × 100 |
| 평균 근속개월 | 근속일수 / 30.4375. 재직: `report_date − hired_at`, 퇴사: `resigned_at − hired_at`. `report_date`는 `date_to` 또는 `CURRENT_DATE` |

차트는 현재 재직(`status=active`) 배치 기준입니다. 과거 라인 이력은 없습니다.
퇴사는 **인원 수**만 보여 줍니다. 일별 재직 스냅샷이 없어 turnover rate는 계산하지 않습니다.

근속 구간(재직만): 0~6개월 / 6~12개월 / 1~3년 / 3년 이상.

---

## 정합성

점수를 만들지 않습니다. 항목별 **건수**만 보여 줍니다.
제약으로 막히는 항목도 0으로 조회합니다. 0인 것도 조회 결과입니다.

입력 시 막는 것:

- `employee_number` UNIQUE
- `(employee_id, work_date)` UNIQUE
- `(production_line_id, factory_id)` → `production_lines(id, factory_id)` 복합 FK
- 업무 FK `ON DELETE RESTRICT` (직원 삭제가 근태를 cascade로 지우지 않음)
- 근무 0~16, 잔업 0~8 check
- 입사 전 / 퇴사 후 근태: trigger + API
- 입사·퇴사일을 줄이면 기존 근태와 충돌 시 `409`

대시보드에서 다시 세는 것:

- 중복 사번
- 직원/날짜 중복 근태
- 비정상 근무시간 · 잔업시간
- 입사 전 근태 · 퇴사 후 근태
- 공장-라인 불일치

---

## 리포트와 AI

`/reports`에서 조회 조건을 건 뒤 받습니다. 생성은 FastAPI입니다.

| | |
|---|---|
| PDF | `GET /api/reports/workforce.pdf` |
| 직원 CSV | `GET /api/reports/employees.csv` |
| 근태 CSV | `GET /api/reports/attendance.csv` |
| AI 요약 | `POST /api/reports/ai-summary` |

PDF 순서: 표지 → 핵심 지표 → 인력 구성 → 근태·잔업 → 근속·퇴사 → 정합성 → 정의와 한계.

한글은 Noto Sans CJK 또는 맑은 고딕을 찾습니다. 없으면 경고를 넣고 Helvetica로 만듭니다.
CSV는 UTF-8 BOM입니다.

AI는 직원 원문을 보내지 않고, 이미 계산된 KPI JSON만 줍니다.

```json
{
  "observations": [],
  "additional_data_needed": [],
  "cannot_conclude": []
}
```

제공된 KPI 밖의 사실을 만들지 않고, 원인을 단정하지 않으며, 해고·채용을 추천하지 않습니다.
`GEMINI_API_KEY`가 없으면 이 API만 `503`이고 PDF·CSV·화면은 그대로입니다.

---

## 스키마와 코드 구조

```text
departments          factories
      │                  │
      │                  ├── production_lines
      │                  │
      └──────── employees ──────── shifts
                    │
                    └── attendance
```

스키마 변경은 `create_all()`이 아니라 Alembic입니다. head: `20260828_0002`.

```text
.
├── frontend/          app, components, lib/api.ts, tests
├── backend/
│   ├── app/           models, routers, services, query.py
│   ├── alembic/
│   ├── scripts/seed.py
│   └── tests/
├── .github/workflows/ci.yml
├── docker-compose.yml
├── .env.example
├── LICENSE
└── README.md
```

교차 검증·KPI·PDF/CSV/AI는 `backend/app/services/`에 있습니다.
프론트 API 호출은 `frontend/lib/api.ts` 한곳입니다.

---

## 실행

`.env.example`을 `.env`로 복사합니다. `GEMINI_API_KEY`는 비워 두어도 됩니다.
키는 Git에 넣지 않습니다.

### Docker Compose

```powershell
Copy-Item .env.example .env
docker compose up --build
```

http://localhost:3000 · API http://localhost:8000 · Swagger `/docs`

컨테이너는 DB healthy 이후 기동하고, 시작 시 `alembic upgrade head`와 seed를 돌립니다.
직원이 있으면 seed는 건너뜁니다.

이 저장소를 작업한 Windows 환경에는 Docker CLI가 없어 compose 기동은 여기서 확인하지 못했습니다.

### 로컬

PostgreSQL이 `DATABASE_URL`에 붙는 상태에서:

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

```powershell
Set-Location frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Seed(빈 직원 테이블): 부서 4, 공장 2, 생산라인 6, 교대조 2, 직원 50, 근태 1,070.
난수 시드 `20260828`.

### 테스트

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

| 항목 | 결과 |
|---|---|
| Backend pytest | **35 passed** (기존 CRUD 23 + 집계/리포트 12) |
| Frontend vitest | **7 passed** |
| lint / typecheck / build | passed (Next.js 15.5.24) |
| Alembic | `20260828_0002` |
| Seed | 직원 50, 근태 1,070 |
| GitHub Actions | 워크플로 있음. remote 실행 여부는 적지 않음 |
| Docker Compose up | 미실행 (Docker CLI 없음) |

---

## API

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

직원 목록 쿼리: `page`, `page_size`, `name`, 조직 필터, `status`.
근태 목록: `employee_id`, `date_from`, `date_to`, `attendance_status`.
생산라인은 `factory_id`로 좁힐 수 있습니다.
`summary`는 기존 필드를 유지하고 `resigned_in_period` 등을 더했습니다.

---

## 한계

- seed는 실제 HRIS가 아닌 고정 난수
- 출입기·ERP 연동 없음. 생산량·품질·임금 없음
- 배치 이력이 없음. 근태의 공장/라인/교대는 **현재** 배치
- 인증 없음
- 근태·퇴사 숫자로 원인을 단정할 수 없음
- AI는 계산된 KPI의 보조 요약. 노무 판단용이 아님
- PDF 한글은 시스템 CJK 폰트에 의존

이후에 넣을 수 있는 것: 배치 이력, Admin/Viewer, HRIS 연동, 생산량 조인, 배포, E2E.

---

## 구현 메모

**직원 삭제.** FK는 `RESTRICT`, 근태가 있으면 API `409`. 운영 데이터를 cascade로 지우는 쪽이 더 위험하다고 봤습니다.

**공장-라인.** 라인 ID만 두면 다른 공장 라인을 고를 수 있습니다. 복합 FK와 서비스 검증을 같이 두고, 테스트는 `400`과 `IntegrityError`를 둘 다 봅니다.

**입사일/퇴사일 수정.** 날짜 형식만 보면 기존 근태가 새 입사일 이전이 됩니다. 수정 전 해당 직원의 최소/최대 `work_date`를 보고 충돌하면 `409`입니다.

**점수 없음.** 99점 같은 값은 분모와 가중치를 설명하기 어렵습니다. 항목별 건수만 둡니다.

**퇴사율 없음.** turnover의 분모는 보통 기간 평균 재직입니다. 일별 스냅샷이 없어 기간 내 퇴사 인원만 집계합니다.

**AI 입력.** 테이블 dump는 없는 사실을 만들기 쉽습니다. 집계 JSON만 보내고 `cannot_conclude`을 필수로 두었습니다. 키가 없으면 앱 전체가 죽지 않습니다.

**기존 pytest 23개**는 계약을 바꾸지 않는 기준으로 남겼습니다. summary 필드는 빼지 않았습니다.

---

## License

MIT. [LICENSE](./LICENSE)

## Author

ssg-sak · [GitHub](https://github.com/ssg-sak) · [FactoryHR-Lite](https://github.com/ssg-sak/FactoryHR-Lite)
