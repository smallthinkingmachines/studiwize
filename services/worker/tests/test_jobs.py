from fastapi.testclient import TestClient

from studiwize_worker.main import app

client = TestClient(app)


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_job_lifecycle() -> None:
    create = client.post(
        "/jobs", json={"source_key": "books/abc.pdf", "chapter_index": 0}
    )
    assert create.status_code == 202
    job_id = create.json()["job_id"]

    fetched = client.get(f"/jobs/{job_id}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "pending"

    cancelled = client.delete(f"/jobs/{job_id}")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_get_missing_job() -> None:
    resp = client.get("/jobs/does-not-exist")
    assert resp.status_code == 404
