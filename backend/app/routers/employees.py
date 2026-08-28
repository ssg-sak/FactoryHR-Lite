from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AdminUser, CurrentUser
from app.models.employee import EmployeeStatus
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.services import employee_service

router = APIRouter(prefix="/api/employees", tags=["Employees"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=EmployeeListResponse, summary="직원 목록과 검색")
def get_employees(
    db: DbSession,
    _user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    name: str | None = None,
    department_id: int | None = None,
    factory_id: int | None = None,
    production_line_id: int | None = None,
    shift_id: int | None = None,
    status_filter: Annotated[EmployeeStatus | None, Query(alias="status")] = None,
) -> dict[str, object]:
    employees, total = employee_service.list_employees(
        db,
        page=page,
        page_size=page_size,
        name=name,
        department_id=department_id,
        factory_id=factory_id,
        production_line_id=production_line_id,
        shift_id=shift_id,
        employee_status=status_filter,
    )
    return {
        "items": [employee_service.employee_response(item) for item in employees],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED, summary="직원 등록"
)
def post_employee(
    payload: EmployeeCreate, db: DbSession, _user: AdminUser
) -> dict[str, object]:
    return employee_service.employee_response(
        employee_service.create_employee(db, payload)
    )


@router.get("/{employee_id}", response_model=EmployeeResponse, summary="직원 상세")
def get_employee(
    employee_id: int, db: DbSession, _user: CurrentUser
) -> dict[str, object]:
    return employee_service.employee_response(
        employee_service.get_employee_or_404(db, employee_id)
    )


@router.patch("/{employee_id}", response_model=EmployeeResponse, summary="직원 수정")
def patch_employee(
    employee_id: int, payload: EmployeeUpdate, db: DbSession, _user: AdminUser
) -> dict[str, object]:
    return employee_service.employee_response(
        employee_service.update_employee(db, employee_id, payload)
    )


@router.delete(
    "/{employee_id}", status_code=status.HTTP_204_NO_CONTENT, summary="직원 삭제"
)
def remove_employee(
    employee_id: int, db: DbSession, _user: AdminUser
) -> Response:
    employee_service.delete_employee(db, employee_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

