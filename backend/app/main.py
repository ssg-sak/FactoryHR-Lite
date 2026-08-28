from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import SessionLocal
from app.routers import attendance, dashboard, employees, master_data, reports

app = FastAPI(
    title=settings.app_name,
    description="제조업 현장의 직원·배치·근태 운영 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(dashboard.router)
app.include_router(master_data.router)
app.include_router(reports.router)


@app.get("/health", tags=["System"], summary="애플리케이션과 DB 연결 확인")
def health_check() -> JSONResponse:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "disconnected"},
        )
    return JSONResponse(
        status_code=200, content={"status": "ok", "database": "connected"}
    )
