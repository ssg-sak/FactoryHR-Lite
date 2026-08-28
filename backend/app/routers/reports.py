from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.query import WorkforceQuery
from app.schemas.dashboard import AISummaryResponse
from app.services.ai_service import generate_ai_summary
from app.services.csv_service import attendance_csv, employees_csv, report_filename_stamp
from app.services.pdf_service import build_workforce_pdf
from app.services.report_payload import build_report_payload

router = APIRouter(prefix="/api/reports", tags=["Reports"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/workforce.pdf", summary="인력·근태 PDF 리포트")
def workforce_pdf(db: DbSession, filters: WorkforceQuery) -> Response:
    payload = build_report_payload(db, filters)
    content = build_workforce_pdf(payload)
    filename = f"factoryhr_workforce_report_{report_filename_stamp()}.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/employees.csv", summary="직원 CSV 내보내기")
def export_employees_csv(db: DbSession, filters: WorkforceQuery) -> Response:
    filename = f"factoryhr_employees_{report_filename_stamp()}.csv"
    return Response(
        content=employees_csv(db, filters),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/attendance.csv", summary="근태 CSV 내보내기")
def export_attendance_csv(db: DbSession, filters: WorkforceQuery) -> Response:
    filename = f"factoryhr_attendance_{report_filename_stamp()}.csv"
    return Response(
        content=attendance_csv(db, filters),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/ai-summary",
    response_model=AISummaryResponse,
    summary="구조화 KPI 기반 AI HR 요약",
)
def ai_summary(db: DbSession, filters: WorkforceQuery) -> dict[str, list[str]]:
    payload = build_report_payload(db, filters)
    return generate_ai_summary(payload)
