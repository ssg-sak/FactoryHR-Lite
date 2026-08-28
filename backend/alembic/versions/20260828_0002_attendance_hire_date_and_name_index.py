"""protect attendance hire dates and index employee names

Revision ID: 20260828_0002
Revises: 20260828_0001
Create Date: 2026-08-28
"""
from collections.abc import Sequence

from alembic import op

revision: str = "20260828_0002"
down_revision: str | None = "20260828_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_employees_name", "employees", ["name"])
    op.execute(
        """
        CREATE OR REPLACE FUNCTION check_attendance_employment_date()
        RETURNS trigger AS $$
        DECLARE
            employee_hired_at date;
            employee_resigned_at date;
        BEGIN
            SELECT hired_at, resigned_at
            INTO employee_hired_at, employee_resigned_at
            FROM employees
            WHERE id = NEW.employee_id;

            IF employee_hired_at IS NOT NULL AND NEW.work_date < employee_hired_at THEN
                RAISE EXCEPTION
                    'attendance date % is before employee % hire date %',
                    NEW.work_date, NEW.employee_id, employee_hired_at
                    USING ERRCODE = '23514';
            END IF;
            IF employee_resigned_at IS NOT NULL AND NEW.work_date > employee_resigned_at THEN
                RAISE EXCEPTION
                    'attendance date % is after employee % resignation date %',
                    NEW.work_date, NEW.employee_id, employee_resigned_at
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute("DROP TRIGGER trg_employee_resignation_attendance ON employees")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION check_employee_resignation_attendance()
        RETURNS trigger AS $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM attendance
                WHERE employee_id = NEW.id AND work_date < NEW.hired_at
            ) THEN
                RAISE EXCEPTION
                    'employee % has attendance before hire date %',
                    NEW.id, NEW.hired_at
                    USING ERRCODE = '23514';
            END IF;
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
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_employee_resignation_attendance
        BEFORE UPDATE OF hired_at, resigned_at, status ON employees
        FOR EACH ROW EXECUTE FUNCTION check_employee_resignation_attendance()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER trg_employee_resignation_attendance ON employees")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION check_employee_resignation_attendance()
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
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_employee_resignation_attendance
        BEFORE UPDATE OF resigned_at, status ON employees
        FOR EACH ROW EXECUTE FUNCTION check_employee_resignation_attendance()
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION check_attendance_employment_date()
        RETURNS trigger AS $$
        DECLARE
            employee_resigned_at date;
        BEGIN
            SELECT resigned_at INTO employee_resigned_at
            FROM employees
            WHERE id = NEW.employee_id;
            IF employee_resigned_at IS NOT NULL AND NEW.work_date > employee_resigned_at THEN
                RAISE EXCEPTION
                    'attendance date % is after employee % resignation date %',
                    NEW.work_date, NEW.employee_id, employee_resigned_at
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.drop_index("ix_employees_name", table_name="employees")

