from fastapi.testclient import TestClient


def test_dashboard_summary(client: TestClient) -> None:
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_employees"] == 3
    assert data["active_employees"] == 2
    assert data["resigned_employees"] == 1
    assert data["attendance_records"] == 3
    assert data["absence_rate"] == 33.33
    assert data["late_rate"] == 33.33
    assert data["average_overtime_hours"] == 1.0
    assert sum(item["count"] for item in data["employees_by_shift"]) == 3
    assert sum(item["count"] for item in data["employees_by_line"]) == 2


def test_dashboard_date_filter(client: TestClient) -> None:
    data = client.get(
        "/api/dashboard/summary",
        params={"date_from": "2026-01-11", "date_to": "2026-01-11"},
    ).json()
    assert data["attendance_records"] == 1
    assert data["absence_rate"] == 100.0


def test_master_data_and_line_filter(client: TestClient) -> None:
    assert len(client.get("/api/departments").json()) == 2
    assert len(client.get("/api/factories").json()) == 2
    assert len(client.get("/api/shifts").json()) == 2
    lines = client.get("/api/production-lines", params={"factory_id": 1}).json()
    assert len(lines) == 1
    assert lines[0]["factory_name"] == "대구1공장"


def test_health_checks_database(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
