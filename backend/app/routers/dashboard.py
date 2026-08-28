from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.query import WorkforceQuery
from app.schemas.dashboard import (
    AttendanceTrendResponse,
    DashboardSummaryResponse,
    DataQualityResponse,
    OvertimeSummaryResponse,
    TenureDistributionResponse,
    WorkforceDistributionResponse,
)
from app.services.dashboard_service import (
    get_attendance_trend,
    get_dashboard_summary,
    get_overtime_summary,
    get_tenure_distribution,
    get_workforce_distribution,
)
from app.services.data_quality_service import get_data_quality

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/summary", response_model=DashboardSummaryResponse, summary="HR 운영 대시보드 집계"
)
def dashboard_summary(
    db: DbSession,
    date_from: date | None = None,
    date_to: date | None = None,
    department_id: Annotated[int | None, Query(gt=0)] = None,
    factory_id: Annotated[int | None, Query(gt=0)] = None,
    production_line_id: Annotated[int | None, Query(gt=0)] = None,
    shift_id: Annotated[int | None, Query(gt=0)] = None,
) -> dict[str, object]:
    return get_dashboard_summary(
        db,
        date_from=date_from,
        date_to=date_to,
        department_id=department_id,
        factory_id=factory_id,
        production_line_id=production_line_id,
        shift_id=shift_id,
    )


@router.get(
    "/workforce-distribution",
    response_model=WorkforceDistributionResponse,
    summary="재직 인원 분포와 기간 내 퇴사 인원",
)
def workforce_distribution(
    db: DbSession, filters: WorkforceQuery
) -> dict[str, object]:
    return get_workforce_distribution(db, filters)


@router.get(
    "/attendance-trend",
    response_model=AttendanceTrendResponse,
    summary="날짜별 근태 추이",
)
def attendance_trend(db: DbSession, filters: WorkforceQuery) -> dict[str, object]:
    return get_attendance_trend(db, filters)


@router.get(
    "/overtime",
    response_model=OvertimeSummaryResponse,
    summary="생산라인·교대조별 평균 잔업",
)
def overtime_summary(db: DbSession, filters: WorkforceQuery) -> dict[str, object]:
    return get_overtime_summary(db, filters)


@router.get(
    "/tenure-distribution",
    response_model=TenureDistributionResponse,
    summary="재직 직원 근속기간 분포",
)
def tenure_distribution(db: DbSession, filters: WorkforceQuery) -> dict[str, object]:
    return get_tenure_distribution(db, filters)


@router.get(
    "/data-quality",
    response_model=DataQualityResponse,
    summary="데이터베이스 정합성 검사 결과",
)
def data_quality(db: DbSession) -> dict[str, int]:
    return get_data_quality(db)
