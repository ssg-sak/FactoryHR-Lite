from fastapi.testclient import TestClient


def employee_payload(ids: dict[str, int], number: str = "FHR-0100") -> dict[str, object]:
    return {
        "employee_number": number,
        "name": "최수아",
        "department_id": ids["prod"],
        "factory_id": ids["daegu"],
        "production_line_id": ids["daegu_line"],
        "shift_id": ids["day"],
        "position": "사원",
        "hired_at": "2025-01-01",
        "status": "active",
    }


def test_create_employee(client: TestClient, reference_ids: dict[str, int]) -> None:
    response = client.post("/api/employees", json=employee_payload(reference_ids))
    assert response.status_code == 201
    assert response.json()["department_name"] == "생산"
    assert response.json()["factory_name"] == "대구1공장"


def test_duplicate_employee_number(
    client: TestClient, reference_ids: dict[str, int]
) -> None:
    response = client.post(
        "/api/employees", json=employee_payload(reference_ids, "FHR-0001")
    )
    assert response.status_code == 409


def test_employee_list_search_and_filters(
    client: TestClient, reference_ids: dict[str, int]
) -> None:
    assert client.get("/api/employees").json()["total"] == 3
    search = client.get("/api/employees", params={"name": "김"}).json()
    assert search["total"] == 1
    assert search["items"][0]["name"] == "김민준"
    department = client.get(
        "/api/employees", params={"department_id": reference_ids["qa"]}
    ).json()
    assert department["total"] == 1
    shift = client.get(
        "/api/employees", params={"shift_id": reference_ids["night"]}
    ).json()
    assert shift["total"] == 1


def test_employee_detail_and_not_found(client: TestClient) -> None:
    assert client.get("/api/employees/1").status_code == 200
    assert client.get("/api/employees/9999").status_code == 404


def test_update_employee(client: TestClient) -> None:
    response = client.patch("/api/employees/2", json={"position": "대리"})
    assert response.status_code == 200
    assert response.json()["position"] == "대리"


def test_invalid_employment_dates(client: TestClient) -> None:
    response = client.patch(
        "/api/employees/2",
        json={"status": "resigned", "resigned_at": "2024-05-01"},
    )
    assert response.status_code == 400


def test_invalid_factory_line(client: TestClient, reference_ids: dict[str, int]) -> None:
    payload = employee_payload(reference_ids)
    payload["production_line_id"] = reference_ids["gumi_line"]
    response = client.post("/api/employees", json=payload)
    assert response.status_code == 400


def test_employee_delete_policy(client: TestClient) -> None:
    assert client.delete("/api/employees/1").status_code == 409
    assert client.delete("/api/employees/2").status_code == 204
    assert client.get("/api/employees/2").status_code == 404
