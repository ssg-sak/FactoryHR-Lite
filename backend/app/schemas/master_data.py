from datetime import time

from pydantic import BaseModel, ConfigDict


class DepartmentResponse(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class FactoryResponse(DepartmentResponse):
    location: str | None


class ProductionLineResponse(DepartmentResponse):
    factory_id: int
    factory_name: str


class ShiftResponse(DepartmentResponse):
    start_time: time | None
    end_time: time | None
