from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Employee


def test_employee_number_unique(db: Session, reference_ids: dict[str, int]) -> None:
    db.add(
        Employee(
            employee_number="FHR-0001",
            name="중복",
            department_id=reference_ids["prod"],
            factory_id=reference_ids["daegu"],
            production_line_id=reference_ids["daegu_line"],
            shift_id=reference_ids["day"],
            hired_at=date(2025, 1, 1),
            status="active",
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_factory_line_composite_fk(db: Session, reference_ids: dict[str, int]) -> None:
    db.add(
        Employee(
            employee_number="FHR-0099",
            name="공장불일치",
            department_id=reference_ids["prod"],
            factory_id=reference_ids["daegu"],
            production_line_id=reference_ids["gumi_line"],
            shift_id=reference_ids["day"],
            hired_at=date(2025, 1, 1),
            status="active",
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

