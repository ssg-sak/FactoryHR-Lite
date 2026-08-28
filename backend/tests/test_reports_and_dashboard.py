import json
from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def test_dashboard_org_filter(client: TestClient, reference_ids: dict[str, int]) -> None:
    data = client.get(
        "/api/dashboard/summary",
        params={"factory_id": reference_ids["daegu"]},
    ).json()
    assert data["total_employees"] == 2
    assert data["active_employees"] == 2
    assert data["resigned_employees"] == 0
    assert data["attendance_records"] == 2
    assert data["resigned_in_period"] == 0


def test_dashboard_resigned_in_period(client: TestClient) -> None:
    in_range = client.get(
        "/api/dashboard/summary",
        params={"date_from": "2026-01-01", "date_to": "2026-01-31"},
    ).json()
    assert in_range["resigned_in_period"] == 1
    out_of_range = client.get(
        "/api/dashboard/summary",
        params={"date_from": "2026-02-01", "date_to": "2026-02-28"},
    ).json()
    assert out_of_range["resigned_in_period"] == 0
    assert out_of_range["attendance_records"] == 0


def test_workforce_distribution_active_only(client: TestClient) -> None:
    data = client.get("/api/dashboard/workforce-distribution").json()
    factory_counts = {item["name"]: item["count"] for item in data["active_by_factory"]}
    assert factory_counts["대구1공장"] == 2
    assert factory_counts["구미1공장"] == 0
    shift_total = sum(item["count"] for item in data["active_by_shift"])
    assert shift_total == 2
    resignations = {
        item["name"]: item["count"] for item in data["resignations_by_department"]
    }
    assert resignations["생산"] == 1


def test_attendance_trend_and_overtime(client: TestClient) -> None:
    trend = client.get(
        "/api/dashboard/attendance-trend",
        params={"date_from": "2026-01-10", "date_to": "2026-01-15"},
    ).json()
    assert len(trend["points"]) == 3
    absent_day = next(p for p in trend["points"] if p["work_date"] == "2026-01-11")
    assert absent_day["absent"] == 1
    assert absent_day["absence_rate"] == 100.0

    overtime = client.get("/api/dashboard/overtime").json()
    assert overtime["by_shift"]
    assert overtime["by_production_line"]
    day = next(item for item in overtime["by_shift"] if item["name"] == "주간조")
    assert day["average_overtime_hours"] == 1.0


def test_tenure_distribution(client: TestClient) -> None:
    data = client.get(
        "/api/dashboard/tenure-distribution",
        params={"date_to": "2026-08-28"},
    ).json()
    counts = {item["key"]: item["count"] for item in data["bands"]}
    assert counts["12_36"] == 2
    assert sum(counts.values()) == 2


def test_data_quality_endpoint(client: TestClient) -> None:
    data = client.get("/api/dashboard/data-quality").json()
    assert data["total_employees"] == 3
    assert data["total_attendance_records"] == 3
    assert data["duplicate_employee_numbers"] == 0
    assert data["duplicate_attendance"] == 0
    assert data["invalid_work_hours"] == 0
    assert data["invalid_overtime_hours"] == 0
    assert data["attendance_before_hire_date"] == 0
    assert data["attendance_after_resignation"] == 0
    assert data["factory_line_mismatch"] == 0


def test_pdf_report(client: TestClient) -> None:
    response = client.get(
        "/api/reports/workforce.pdf",
        params={"date_from": "2026-01-01", "date_to": "2026-01-31"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    disposition = response.headers["content-disposition"]
    assert "attachment" in disposition
    assert disposition.endswith('.pdf"') or disposition.endswith(".pdf")
    assert len(response.content) > 500
    assert response.content[:4] == b"%PDF"


def test_csv_employees_and_filter(
    client: TestClient, reference_ids: dict[str, int]
) -> None:
    response = client.get("/api/reports/employees.csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    body = response.content
    assert body.startswith(b"\xef\xbb\xbf")
    text = body.decode("utf-8-sig")
    assert "FHR-0001" in text
    assert "FHR-0003" in text

    filtered = client.get(
        "/api/reports/employees.csv",
        params={"factory_id": reference_ids["daegu"]},
    )
    filtered_text = filtered.content.decode("utf-8-sig")
    assert "FHR-0001" in filtered_text
    assert "FHR-0003" not in filtered_text


def test_csv_attendance_date_filter(client: TestClient) -> None:
    response = client.get(
        "/api/reports/attendance.csv",
        params={"date_from": "2026-01-11", "date_to": "2026-01-11"},
    )
    assert response.status_code == 200
    text = response.content.decode("utf-8-sig")
    lines = [line for line in text.splitlines() if line.strip()]
    assert lines[0].startswith("work_date")
    assert len(lines) == 2
    assert "absent" in lines[1]


def test_ai_summary_without_api_key(
    client: TestClient, monkeypatch: object
) -> None:
    monkeypatch.setattr(
        "app.services.ai_service.get_gemini_api_key", lambda: ""
    )
    response = client.post("/api/reports/ai-summary")
    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]


def test_ai_summary_schema_from_mock(
    client: TestClient, monkeypatch: object
) -> None:
    monkeypatch.setattr(
        "app.services.ai_service.get_gemini_api_key", lambda: "test-key"
    )
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "observations": ["야간조 평균 잔업이 더 높았습니다."],
                                    "additional_data_needed": ["생산량 데이터"],
                                    "cannot_conclude": ["퇴사 원인"],
                                }
                            )
                        }
                    ]
                }
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = payload
    monkeypatch.setattr("app.services.ai_service.httpx.post", lambda *a, **k: mock_response)
    response = client.post("/api/reports/ai-summary")
    assert response.status_code == 200
    body = response.json()
    assert body["observations"] == ["야간조 평균 잔업이 더 높았습니다."]
    assert body["additional_data_needed"] == ["생산량 데이터"]
    assert body["cannot_conclude"] == ["퇴사 원인"]


def test_ai_summary_rejects_invalid_schema(
    client: TestClient, monkeypatch: object
) -> None:
    monkeypatch.setattr(
        "app.services.ai_service.get_gemini_api_key", lambda: "test-key"
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": '{"observations": 1}'}]}}]
    }
    monkeypatch.setattr("app.services.ai_service.httpx.post", lambda *a, **k: mock_response)
    response = client.post("/api/reports/ai-summary")
    assert response.status_code == 502
