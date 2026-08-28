from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.attendance import AttendanceStatus
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceListResponse,
    AttendanceResponse,
    AttendanceUpdate,
)
from app.services import attendance_service

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=AttendanceListResponse, summary="근태 목록과 필터")
def get_attendance(
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    employee_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    attendance_status: AttendanceStatus | None = None,
) -> dict[str, object]:
    records, total = attendance_service.list_attendance(
        db,
        page=page,
        page_size=page_size,
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
        attendance_status=attendance_status,
    )
    return {
        "items": [attendance_service.attendance_response(item) for item in records],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="근태 등록",
)
def post_attendance(payload: AttendanceCreate, db: DbSession) -> dict[str, object]:
    return attendance_service.attendance_response(
        attendance_service.create_attendance(db, payload)
    )


@router.get(
    "/{attendance_id}", response_model=AttendanceResponse, summary="근태 상세"
)
def get_attendance_detail(attendance_id: int, db: DbSession) -> dict[str, object]:
    return attendance_service.attendance_response(
        attendance_service.get_attendance_or_404(db, attendance_id)
    )


@router.patch(
    "/{attendance_id}", response_model=AttendanceResponse, summary="근태 수정"
)
def patch_attendance(
    attendance_id: int, payload: AttendanceUpdate, db: DbSession
) -> dict[str, object]:
    return attendance_service.attendance_response(
        attendance_service.update_attendance(db, attendance_id, payload)
    )


@router.delete(
    "/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT, summary="근태 삭제"
)
def remove_attendance(attendance_id: int, db: DbSession) -> Response:
    attendance_service.delete_attendance(db, attendance_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

