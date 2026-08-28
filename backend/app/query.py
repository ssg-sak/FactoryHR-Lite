from datetime import date
from typing import Annotated

from fastapi import Depends, Query

from app.services.filters import WorkforceFilters


def workforce_query(
    date_from: date | None = None,
    date_to: date | None = None,
    department_id: Annotated[int | None, Query(gt=0)] = None,
    factory_id: Annotated[int | None, Query(gt=0)] = None,
    production_line_id: Annotated[int | None, Query(gt=0)] = None,
    shift_id: Annotated[int | None, Query(gt=0)] = None,
) -> WorkforceFilters:
    filters = WorkforceFilters(
        date_from=date_from,
        date_to=date_to,
        department_id=department_id,
        factory_id=factory_id,
        production_line_id=production_line_id,
        shift_id=shift_id,
    )
    filters.validate()
    return filters


WorkforceQuery = Annotated[WorkforceFilters, Depends(workforce_query)]
