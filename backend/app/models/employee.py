import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.attendance import Attendance
    from app.models.department import Department
    from app.models.factory import Factory
    from app.models.production_line import ProductionLine
    from app.models.shift import Shift


class EmployeeStatus(str, enum.Enum):
    ACTIVE = "active"
    RESIGNED = "resigned"


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (
        ForeignKeyConstraint(
            ["production_line_id", "factory_id"],
            ["production_lines.id", "production_lines.factory_id"],
            name="fk_employees_line_factory",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "resigned_at IS NULL OR resigned_at >= hired_at",
            name="ck_employees_resigned_after_hired",
        ),
        CheckConstraint(
            "(status = 'active' AND resigned_at IS NULL) OR "
            "(status = 'resigned' AND resigned_at IS NOT NULL)",
            name="ck_employees_status_resigned_at",
        ),
        CheckConstraint(
            "status IN ('active', 'resigned')", name="ck_employees_status_values"
        ),
        Index("ix_employees_name", "name"),
        Index("ix_employees_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_number: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    production_line_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    shift_id: Mapped[int] = mapped_column(
        ForeignKey("shifts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    position: Mapped[str | None] = mapped_column(String(100))
    hired_at: Mapped[date] = mapped_column(Date, nullable=False)
    resigned_at: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EmployeeStatus.ACTIVE.value
    )

    department: Mapped["Department"] = relationship(back_populates="employees")
    factory: Mapped["Factory"] = relationship(
        back_populates="employees", foreign_keys=[factory_id]
    )
    production_line: Mapped["ProductionLine | None"] = relationship(
        back_populates="employees",
        primaryjoin="Employee.production_line_id == ProductionLine.id",
        foreign_keys=[production_line_id],
    )
    shift: Mapped["Shift"] = relationship(back_populates="employees")
    attendance_records: Mapped[list["Attendance"]] = relationship(
        back_populates="employee", passive_deletes=True
    )
