import enum
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"
    LEAVE = "leave"


class Attendance(TimestampMixin, Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_date"),
        CheckConstraint(
            "work_hours >= 0 AND work_hours <= 16", name="ck_attendance_work_hours"
        ),
        CheckConstraint(
            "overtime_hours >= 0 AND overtime_hours <= 8",
            name="ck_attendance_overtime_hours",
        ),
        CheckConstraint(
            "attendance_status IN ('present', 'late', 'absent', 'leave')",
            name="ck_attendance_status_values",
        ),
        Index("ix_attendance_work_date", "work_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    work_hours: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), nullable=False, default=Decimal("0"), server_default="0"
    )
    overtime_hours: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), nullable=False, default=Decimal("0"), server_default="0"
    )
    attendance_status: Mapped[str] = mapped_column(String(20), nullable=False)

    employee: Mapped["Employee"] = relationship(back_populates="attendance_records")

