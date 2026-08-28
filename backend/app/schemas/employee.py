from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.employee import EmployeeStatus


def validate_employment_dates(
    hired_at: date, resigned_at: date | None, status: EmployeeStatus
) -> None:
    if resigned_at is not None and resigned_at < hired_at:
        raise ValueError("resigned_at must be on or after hired_at")
    if status == EmployeeStatus.ACTIVE and resigned_at is not None:
        raise ValueError("active employees cannot have resigned_at")
    if status == EmployeeStatus.RESIGNED and resigned_at is None:
        raise ValueError("resigned employees require resigned_at")


class EmployeeBase(BaseModel):
    employee_number: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=100)
    department_id: int = Field(gt=0)
    factory_id: int = Field(gt=0)
    production_line_id: int | None = Field(default=None, gt=0)
    shift_id: int = Field(gt=0)
    position: str | None = Field(default=None, max_length=100)
    hired_at: date
    resigned_at: date | None = None
    status: EmployeeStatus = EmployeeStatus.ACTIVE

    @model_validator(mode="after")
    def validate_employment_period(self) -> "EmployeeBase":
        validate_employment_dates(self.hired_at, self.resigned_at, self.status)
        return self


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    employee_number: str | None = Field(default=None, min_length=1, max_length=30)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    department_id: int | None = Field(default=None, gt=0)
    factory_id: int | None = Field(default=None, gt=0)
    production_line_id: int | None = Field(default=None, gt=0)
    shift_id: int | None = Field(default=None, gt=0)
    position: str | None = Field(default=None, max_length=100)
    hired_at: date | None = None
    resigned_at: date | None = None
    status: EmployeeStatus | None = None


class EmployeeResponse(EmployeeBase):
    id: int
    department_name: str
    factory_name: str
    production_line_name: str | None
    shift_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeListResponse(BaseModel):
    items: list[EmployeeResponse]
    total: int
    page: int
    page_size: int

