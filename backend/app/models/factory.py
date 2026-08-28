from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.production_line import ProductionLine


class Factory(CreatedAtMixin, Base):
    __tablename__ = "factories"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))

    production_lines: Mapped[list["ProductionLine"]] = relationship(
        back_populates="factory"
    )
    employees: Mapped[list["Employee"]] = relationship(
        back_populates="factory", foreign_keys="Employee.factory_id"
    )

