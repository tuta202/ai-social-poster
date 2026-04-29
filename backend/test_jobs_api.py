"""
Manual smoke test for Jobs API.
Run while uvicorn is running: python test_jobs_api.py
Requires: admin user seeded, backend running at localhost:8000
Note: parse + confirm require OPENAI_API_KEY in .env
"""
import httpx
import json

BASE = "http://localhost:8000"


def get_token() -> str:
    r = httpx.post(f"{BASE}/auth/login", json={"username": "admin", "password": "postpilot2024"})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_parse_job(token: str) -> int:
    """Test SSE parse endpoint -- collect all events."""
    headers = {"Authorization": f"Bearer {token}"}
    event_type = ""
    job_id = None

    with httpx.stream("POST", f"{BASE}/jobs/parse",
                      json={"raw_input": "Create 3 motivation posts over 3 days at 9am"},
                      headers=headers, timeout=60) as r:
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        for line in r.iter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = json.loads(line.split(":", 1)[1].strip())
                if event_type == "done":
                    job_id = data["job_id"]
                    assert "config" in data
                    assert "posts" in data
                    print(f"  Job created: ID={job_id}, posts={len(data['posts'])}")
                elif event_type == "step":
                    print(f"  Step: {data.get('step')} - {data.get('message', '')}")
                elif event_type == "error":
                    print(f"  ERROR: {data}")
                    raise AssertionError(f"Parse failed: {data['message']}")

    assert job_id is not None, "No job_id in done event"
    print(f"Parse job PASS -- job_id={job_id}")
    return job_id


def test_get_job(token: str, job_id: int):
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get(f"{BASE}/jobs/{job_id}", headers=headers)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["id"] == job_id
    assert data["status"] == "DRAFT"
    assert len(data["posts"]) == 3
    print(f"GET /jobs/{job_id} PASS -- {len(data['posts'])} posts, status={data['status']}")


def test_get_job_404(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get(f"{BASE}/jobs/99999", headers=headers)
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    print("GET /jobs/99999 -> 404 PASS")


def test_list_jobs(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get(f"{BASE}/jobs/", headers=headers)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    jobs = r.json()
    assert len(jobs) >= 1
    assert all("total_posts" in j for j in jobs)
    assert all(isinstance(j["total_posts"], int) for j in jobs)
    print(f"GET /jobs/ PASS -- {len(jobs)} jobs, all have total_posts")


def test_pause_draft(token: str, job_id: int):
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.post(f"{BASE}/jobs/{job_id}/pause", headers=headers)
    assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
    assert "Cannot pause" in r.json()["detail"]
    print(f"Pause DRAFT job -> 400 PASS")


def test_update_post(token: str, job_id: int):
    headers = {"Authorization": f"Bearer {token}"}
    # Get the job to find a post_id
    r = httpx.get(f"{BASE}/jobs/{job_id}", headers=headers)
    posts = r.json()["posts"]
    post_id = posts[0]["id"]

    r2 = httpx.put(
        f"{BASE}/jobs/{job_id}/posts/{post_id}",
        json={"content_text": "Updated test content"},
        headers=headers,
    )
    assert r2.status_code == 200, f"Expected 200, got {r2.status_code}: {r2.text}"
    assert r2.json()["content_text"] == "Updated test content"
    print(f"PUT /jobs/{job_id}/posts/{post_id} PASS -- content updated")


def test_delete_draft(token: str, job_id: int):
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.delete(f"{BASE}/jobs/{job_id}", headers=headers)
    assert r.status_code == 204, f"Expected 204, got {r.status_code}: {r.text}"
    r2 = httpx.get(f"{BASE}/jobs/{job_id}", headers=headers)
    assert r2.status_code == 404, f"Expected 404 after delete, got {r2.status_code}"
    print(f"DELETE /jobs/{job_id} PASS -- 204, then 404 confirmed")


def test_parse_unauthenticated():
    r = httpx.post(f"{BASE}/jobs/parse", json={"raw_input": "test"})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print("POST /jobs/parse (no token) -> 401 PASS")


if __name__ == "__main__":
    token = get_token()
    print("Token obtained\n")

    test_parse_unauthenticated()
    job_id = test_parse_job(token)
    test_get_job(token, job_id)
    test_get_job_404(token)
    test_list_jobs(token)
    test_pause_draft(token, job_id)
    test_update_post(token, job_id)
    test_delete_draft(token, job_id)

    print("\nAll Jobs API tests passed!")
    print("NOTE: test_confirm_job requires OPENAI_API_KEY -- run manually when key available.")
