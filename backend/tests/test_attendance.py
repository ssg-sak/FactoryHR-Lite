import pytest
from fastapi.testclient import TestClient


def attendance_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "employee_id": 1,
        "work_date": "2026-02-02",
        "work_hours": 8,
        "overtime_hours": 2,
        "attendance_status": "present",
    }
    payload.update(overrides)
    return payload


def test_create_attendance(client: TestClient) -> None:
    response = client.post("/api/attendance", json=attendance_payload())
    assert response.status_code == 201
    assert response.json()["employee_number"] == "FHR-0001"


@pytest.mark.parametrize(
    "changes",
    [
        {"work_hours": -1},
        {"work_hours": 17},
        {"overtime_hours": 9},
    ],
)
def test_attendance_hour_limits(
    client: TestClient, changes: dict[str, object]
) -> None:
    response = client.post("/api/attendance", json=attendance_payload(**changes))
    assert response.status_code == 422


def test_duplicate_attendance(client: TestClient) -> None:
    response = client.post(
        "/api/attendance",
        json=attendance_payload(work_date="2026-01-10"),
    )
    assert response.status_code == 409


def test_attendance_before_hire(client: TestClient) -> None:
    response = client.post(
        "/api/attendance", json=attendance_payload(work_date="2023-12-31")
    )
    assert response.status_code == 400


def test_attendance_after_resignation(client: TestClient) -> None:
    response = client.post(
        "/api/attendance",
        json=attendance_payload(employee_id=3, work_date="2026-02-01"),
    )
    assert response.status_code == 400


def test_attendance_list_filters(client: TestClient) -> None:
    response = client.get(
        "/api/attendance", params={"attendance_status": "absent"}
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["attendance_status"] == "absent"


def test_attendance_detail_update_delete(client: TestClient) -> None:
    assert client.get("/api/attendance/1").status_code == 200
    updated = client.patch("/api/attendance/1", json={"overtime_hours": 3})
    assert updated.status_code == 200
    assert float(updated.json()["overtime_hours"]) == 3
    assert client.delete("/api/attendance/1").status_code == 204
    assert client.get("/api/attendance/1").status_code == 404

