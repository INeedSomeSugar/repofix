import time

from fastapi.testclient import TestClient

from repofix.api import create_app


def test_api_completes_real_local_execution_without_exposing_grading_code(settings):
    with TestClient(create_app(settings)) as client:
        assert client.get("/").status_code == 200
        assert client.get("/static/app.js").status_code == 200
        cases = client.get("/api/cases").json()
        assert len(cases) == 5 and "heldout" not in str(cases)
        response = client.post("/api/runs", json={"case_id": "csv_records"})
        assert response.status_code == 202
        run_id = response.json()["run_id"]
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            detail = client.get(f"/api/runs/{run_id}").json()
            if detail["status"] not in {"queued", "created", "running"}:
                break
            time.sleep(0.05)
        assert detail["status"] == "verified", detail.get("error_code")
        assert detail["evidence_type"] == "scripted_replay"
        assert "messages" not in detail and "pending_calls" not in detail
        assert detail["patch"] and client.get(f"/api/runs/{run_id}/events").json()
        assert client.get(f"/api/runs/{run_id}/summary").status_code == 200
        assert client.post(f"/api/runs/{run_id}/resume").status_code == 409


def test_api_rejects_missing_credentials_unknown_cases_and_cross_origin(settings):
    with TestClient(create_app(settings)) as client:
        assert client.post("/api/runs", json={"case_id": "bad"}).status_code == 400
        assert (
            client.post(
                "/api/runs",
                json={
                    "case_id": "csv_records",
                    "provider": "deepseek",
                },
            ).status_code
            == 400
        )
        assert (
            client.post(
                "/api/runs",
                json={"case_id": "csv_records"},
                headers={"Origin": "https://foreign.example"},
            ).status_code
            == 403
        )
        assert client.get("/api/runs/not-a-run").status_code == 404
        assert client.get("/", headers={"Host": "foreign.example"}).status_code == 400
