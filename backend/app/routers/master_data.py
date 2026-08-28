from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.master_data import (
    DepartmentResponse,
    FactoryResponse,
    ProductionLineResponse,
    ShiftResponse,
)
from app.services import master_data_service

router = APIRouter(prefix="/api", tags=["Master Data"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/departments", response_model=list[DepartmentResponse])
def get_departments(db: DbSession) -> list[object]:
    return master_data_service.list_departments(db)


@router.get("/factories", response_model=list[FactoryResponse])
def get_factories(db: DbSession) -> list[object]:
    return master_data_service.list_factories(db)


@router.get("/production-lines", response_model=list[ProductionLineResponse])
def get_production_lines(
    db: DbSession, factory_id: int | None = None
) -> list[dict[str, object]]:
    lines = master_data_service.list_production_lines(db, factory_id)
    return [
        {
            "id": line.id,
            "factory_id": line.factory_id,
            "factory_name": line.factory.name,
            "code": line.code,
            "name": line.name,
        }
        for line in lines
    ]


@router.get("/shifts", response_model=list[ShiftResponse])
def get_shifts(db: DbSession) -> list[object]:
    return master_data_service.list_shifts(db)

