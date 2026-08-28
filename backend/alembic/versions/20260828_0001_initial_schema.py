"""create FactoryHR Lite initial schema

Revision ID: 20260828_0001
Revises:
Create Date: 2026-08-28
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260828_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("code", name="uq_departments_code"),
    )
    op.create_table(
        "factories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("code", name="uq_factories_code"),
    )
    op.create_table(
        "shifts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("code", name="uq_shifts_code"),
    )
    op.create_table(
        "production_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("factory_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["factory_id"], ["factories.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "factory_id", "code", name="uq_production_lines_factory_code"
        ),
        sa.UniqueConstraint("id", "factory_id", name="uq_production_lines_id_factory"),
    )
    op.create_index(
        "ix_production_lines_factory_id", "production_lines", ["factory_id"]
    )
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_number", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("factory_id", sa.Integer(), nullable=False),
        sa.Column("production_line_id", sa.Integer(), nullable=True),
        sa.Column("shift_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(length=100), nullable=True),
        sa.Column("hired_at", sa.Date(), nullable=False),
        sa.Column("resigned_at", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "resigned_at IS NULL OR resigned_at >= hired_at",
            name="ck_employees_resigned_after_hired",
        ),
        sa.CheckConstraint(
            "(status = 'active' AND resigned_at IS NULL) OR "
            "(status = 'resigned' AND resigned_at IS NOT NULL)",
            name="ck_employees_status_resigned_at",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'resigned')", name="ck_employees_status_values"
        ),
        sa.ForeignKeyConstraint(
            ["department_id"], ["departments.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["factory_id"], ["factories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["production_line_id", "factory_id"],
            ["production_lines.id", "production_lines.factory_id"],
            name="fk_employees_line_factory",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("employee_number", name="uq_employees_employee_number"),
    )
    op.create_index("ix_employees_department_id", "employees", ["department_id"])
    op.create_index("ix_employees_factory_id", "employees", ["factory_id"])
    op.create_index(
        "ix_employees_production_line_id", "employees", ["production_line_id"]
    )
    op.create_index("ix_employees_shift_id", "employees", ["shift_id"])
    op.create_index("ix_employees_status", "employees", ["status"])
    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column(
            "work_hours", sa.Numeric(precision=4, scale=2), server_default="0", nullable=False
        ),
        sa.Column(
            "overtime_hours",
            sa.Numeric(precision=4, scale=2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("attendance_status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "work_hours >= 0 AND work_hours <= 16", name="ck_attendance_work_hours"
        ),
        sa.CheckConstraint(
            "overtime_hours >= 0 AND overtime_hours <= 8",
            name="ck_attendance_overtime_hours",
        ),
        sa.CheckConstraint(
            "attendance_status IN ('present', 'late', 'absent', 'leave')",
            name="ck_attendance_status_values",
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "employee_id", "work_date", name="uq_attendance_employee_date"
        ),
    )
    op.create_index("ix_attendance_employee_id", "attendance", ["employee_id"])
    op.create_index("ix_attendance_work_date", "attendance", ["work_date"])

    op.execute(
        """
        CREATE FUNCTION check_attendance_employment_date()
        RETURNS trigger AS $$
        DECLARE
            employee_resigned_at date;
        BEGIN
            SELECT resigned_at INTO employee_resigned_at
            FROM employees
            WHERE id = NEW.employee_id;

            IF employee_resigned_at IS NOT NULL
               AND NEW.work_date > employee_resigned_at THEN
                RAISE EXCEPTION
                    'attendance date % is after employee % resignation date %',
                    NEW.work_date, NEW.employee_id, employee_resigned_at
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_attendance_employment_date
        BEFORE INSERT OR UPDATE OF employee_id, work_date ON attendance
        FOR EACH ROW EXECUTE FUNCTION check_attendance_employment_date()
        """
    )
    op.execute(
        """
        CREATE FUNCTION check_employee_resignation_attendance()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.resigned_at IS NOT NULL AND EXISTS (
                SELECT 1 FROM attendance
                WHERE employee_id = NEW.id AND work_date > NEW.resigned_at
            ) THEN
                RAISE EXCEPTION
                    'employee % has attendance after resignation date %',
                    NEW.id, NEW.resigned_at
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_employee_resignation_attendance
        BEFORE UPDATE OF resigned_at, status ON employees
        FOR EACH ROW EXECUTE FUNCTION check_employee_resignation_attendance()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_employee_resignation_attendance ON employees")
    op.execute("DROP FUNCTION IF EXISTS check_employee_resignation_attendance()")
    op.execute("DROP TRIGGER IF EXISTS trg_attendance_employment_date ON attendance")
    op.execute("DROP FUNCTION IF EXISTS check_attendance_employment_date()")
    op.drop_index("ix_attendance_work_date", table_name="attendance")
    op.drop_index("ix_attendance_employee_id", table_name="attendance")
    op.drop_table("attendance")
    op.drop_index("ix_employees_status", table_name="employees")
    op.drop_index("ix_employees_shift_id", table_name="employees")
    op.drop_index("ix_employees_production_line_id", table_name="employees")
    op.drop_index("ix_employees_factory_id", table_name="employees")
    op.drop_index("ix_employees_department_id", table_name="employees")
    op.drop_table("employees")
    op.drop_index("ix_production_lines_factory_id", table_name="production_lines")
    op.drop_table("production_lines")
    op.drop_table("shifts")
    op.drop_table("factories")
    op.drop_table("departments")
