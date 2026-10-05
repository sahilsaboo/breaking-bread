import pytest
from fastapi.testclient import TestClient

from app.main import app

TIKTOK = "https://www.tiktok.com/@cook/video/123"


@pytest.fixture(autouse=True)
def instant_stages(monkeypatch):
    monkeypatch.setenv("STUB_STAGE_SECONDS", "0")


@pytest.fixture
def client():
    return TestClient(app)


def finished_job(client, **body):
    created = client.post("/api/recipes", json=body)
    assert created.status_code == 202
    return client.get(f"/api/jobs/{created.json()['job_id']}").json()


@pytest.mark.parametrize(
    "url",
    [TIKTOK, "https://vm.tiktok.com/ZMabc/", "https://www.instagram.com/reel/Cabc123/"],
)
def test_accepts_supported_links(client, url):
    assert client.post("/api/recipes", json={"url": url}).status_code == 202


@pytest.mark.parametrize(
    "url",
    ["not a link", "https://youtube.com/watch?v=1", "https://www.instagram.com/someuser/"],
)
def test_rejects_unsupported_links(client, url):
    assert client.post("/api/recipes", json={"url": url}).status_code == 422


def test_requires_exactly_one_input(client):
    assert client.post("/api/recipes", json={}).status_code == 422
    assert client.post("/api/recipes", json={"url": TIKTOK, "text": "eggs"}).status_code == 422


def test_link_job_runs_all_stages_and_returns_recipe(client):
    job = finished_job(client, url=TIKTOK)
    assert job["status"] == "done"
    assert job["completed_stages"] == ["metadata", "audio", "frames", "merge"]
    assert job["stages"] == job["completed_stages"]

    recipe = client.get(f"/api/recipes/{job['recipe_id']}").json()
    assert recipe["source_url"] == TIKTOK
    assert len(recipe["ingredients"]) > 0


def test_pasted_text_skips_to_merge_and_tags_source(client):
    job = finished_job(client, text="1 lb chicken, 200g penne")
    assert job["completed_stages"] == ["merge"]

    recipe = client.get(f"/api/recipes/{job['recipe_id']}").json()
    assert {i["source"] for i in recipe["ingredients"]} == {"pasted"}


def test_failed_extraction_reports_error(client):
    job = finished_job(client, url="https://www.tiktok.com/@cook/video/stub-fail")
    assert job["status"] == "failed"
    assert "Paste the caption" in job["error"]


def test_plan_removes_owned_items_from_grocery_list(client):
    recipe_id = finished_job(client, url=TIKTOK)["recipe_id"]

    full = client.post(f"/api/recipes/{recipe_id}/plan", json={"zip_code": "02139"}).json()
    owned = client.post(
        f"/api/recipes/{recipe_id}/plan",
        json={"zip_code": "02139", "owned_ingredient_ids": ["salt", "pepper"]},
    ).json()

    assert len(owned["grocery_list"]) == len(full["grocery_list"]) - 2
    assert owned["costs"]["trip_total"] < full["costs"]["trip_total"]
    assert owned["costs"]["per_meal"] == full["costs"]["per_meal"]
    assert all(item["product"]["price_type"] == "estimate" for item in full["grocery_list"])
    assert sum(i["line_total"] for i in owned["grocery_list"]) == pytest.approx(owned["costs"]["trip_total"])
    assert full["macros_per_serving"]["approximate"] is True


def test_plan_validates_input(client):
    recipe_id = finished_job(client, url=TIKTOK)["recipe_id"]
    path = f"/api/recipes/{recipe_id}/plan"
    assert client.post(path, json={"zip_code": "2139"}).status_code == 422
    assert client.post(path, json={"zip_code": "02139", "owned_ingredient_ids": ["nope"]}).status_code == 422
    assert client.post("/api/recipes/missing/plan", json={"zip_code": "02139"}).status_code == 404
