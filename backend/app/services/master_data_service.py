from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Department, Factory, ProductionLine, Shift


def list_departments(db: Session) -> list[Department]:
    return list(db.scalars(select(Department).order_by(Department.code)))


def list_factories(db: Session) -> list[Factory]:
    return list(db.scalars(select(Factory).order_by(Factory.code)))


def list_production_lines(
    db: Session, factory_id: int | None = None
) -> list[ProductionLine]:
    statement = select(ProductionLine).options(joinedload(ProductionLine.factory))
    if factory_id is not None:
        statement = statement.where(ProductionLine.factory_id == factory_id)
    return list(
        db.scalars(statement.order_by(ProductionLine.factory_id, ProductionLine.code))
    )


def list_shifts(db: Session) -> list[Shift]:
    return list(db.scalars(select(Shift).order_by(Shift.code)))

