from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.factory import Factory


class ProductionLine(CreatedAtMixin, Base):
    __tablename__ = "production_lines"
    __table_args__ = (
        UniqueConstraint("factory_id", "code", name="uq_production_lines_factory_code"),
        UniqueConstraint("id", "factory_id", name="uq_production_lines_id_factory"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    factory: Mapped["Factory"] = relationship(back_populates="production_lines")
    employees: Mapped[list["Employee"]] = relationship(
        back_populates="production_line",
        primaryjoin="ProductionLine.id == Employee.production_line_id",
        foreign_keys="Employee.production_line_id",
    )

