from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import spike_routes
from app.main import app as main_app


def client(monkeypatch, token="secret"):
    monkeypatch.setenv("SPIKE_TOKEN", token)
    app = FastAPI()
    app.include_router(spike_routes.router)
    return TestClient(app)


def test_spike_routes_absent_without_token():
    # SPIKE_TOKEN isn't set in the test environment, so main.py never mounts them.
    assert TestClient(main_app).get("/api/spike").status_code == 404


def test_rejects_missing_or_wrong_token(monkeypatch):
    c = client(monkeypatch)
    assert c.get("/api/spike").status_code == 403
    assert c.get("/api/spike", headers={"X-Spike-Token": "nope"}).status_code == 403
    assert c.post("/api/spike", json={"url": "x"}, headers={"X-Spike-Token": "nope"}).status_code == 403


def test_idle_before_any_run(monkeypatch):
    monkeypatch.setattr(spike_routes, "_proc", None)
    c = client(monkeypatch)
    assert c.get("/api/spike", headers={"X-Spike-Token": "secret"}).json() == {"status": "idle"}
