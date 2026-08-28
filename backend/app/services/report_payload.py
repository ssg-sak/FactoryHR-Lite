from datetime import date

from sqlalchemy.orm import Session

from app.services.dashboard_service import (
    METRIC_DEFINITIONS,
    get_attendance_trend,
    get_dashboard_summary,
    get_overtime_summary,
    get_tenure_distribution,
    get_workforce_distribution,
)
from app.services.data_quality_service import get_data_quality
from app.services.filters import WorkforceFilters
from app.services.master_data_service import (
    list_departments,
    list_factories,
    list_production_lines,
    list_shifts,
)


def resolve_filter_labels(db: Session, filters: WorkforceFilters) -> dict[str, str | None]:
    labels: dict[str, str | None] = {
        "department": None,
        "factory": None,
        "production_line": None,
        "shift": None,
    }
    if filters.department_id is not None:
        for item in list_departments(db):
            if item.id == filters.department_id:
                labels["department"] = item.name
                break
    if filters.factory_id is not None:
        for item in list_factories(db):
            if item.id == filters.factory_id:
                labels["factory"] = item.name
                break
    if filters.production_line_id is not None:
        for item in list_production_lines(db):
            if item.id == filters.production_line_id:
                labels["production_line"] = item.name
                break
    if filters.shift_id is not None:
        for item in list_shifts(db):
            if item.id == filters.shift_id:
                labels["shift"] = item.name
                break
    return labels


def build_report_payload(db: Session, filters: WorkforceFilters) -> dict[str, object]:
    """Structured KPI bundle for PDF, CSV context, and the Gemini prompt."""
    return {
        "filters": {
            **filters.as_dict(),
            "labels": resolve_filter_labels(db, filters),
        },
        "summary": get_dashboard_summary(db, filters=filters),
        "workforce": get_workforce_distribution(db, filters),
        "attendance": get_attendance_trend(db, filters),
        "overtime": get_overtime_summary(db, filters),
        "tenure": get_tenure_distribution(db, filters),
        "data_quality": get_data_quality(db),
        "metric_definitions": METRIC_DEFINITIONS,
        "generated_on": date.today().isoformat(),
    }
