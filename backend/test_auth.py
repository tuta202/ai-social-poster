"""
Quick smoke test — run while uvicorn is running:
  python test_auth.py
"""
import httpx

BASE = "http://localhost:8000"


def test_login():
    r = httpx.post(f"{BASE}/auth/login", json={
        "username": "admin",
        "password": "postpilot2024"
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    data = r.json()
    assert "access_token" in data
    assert data["user"]["username"] == "admin"
    token = data["access_token"]
    print(f"Login OK -- token: {token[:30]}...")
    return token


def test_me(token: str):
    r = httpx.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"Get me failed: {r.text}"
    assert r.json()["username"] == "admin"
    print("GET /auth/me OK")


def test_invalid():
    r = httpx.post(f"{BASE}/auth/login", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print("Invalid login correctly returns 401")


def test_unauthorized():
    r = httpx.get(f"{BASE}/auth/me")
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print("No token correctly returns 401")


if __name__ == "__main__":
    token = test_login()
    test_me(token)
    test_invalid()
    test_unauthorized()
    print("\nAll auth tests passed!")
