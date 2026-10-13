"""The real pipeline, with Claude, yt-dlp, and faster-whisper replaced by fakes."""

import time

import pytest

from app.adapters import claude, transcribe, video
from app.adapters.transcribe import Segment
from app.jobs import Store
from app.models import JobStatus, Servings
from app.pipeline import extract
from app.pipeline.estimates import DraftEstimate, DraftEstimates, to_products_and_macros
from app.pipeline.guidance import DraftGuidance, DraftStep, DraftTerm, to_steps
from app.pipeline.plan import build_plan
from app.pipeline.structure import DraftIngredient, DraftRecipe, to_recipe

URL = "https://www.tiktok.com/@cook/video/123"


def draft_recipe(*, complete=True, source="caption"):
    return DraftRecipe(
        is_recipe=True,
        title="Garlic Butter Rice",
        servings=None,
        complete=complete,
        ingredients=[
            DraftIngredient(name="rice", quantity=1, unit="cup", grams=185, amount_estimated=False, source=source, confidence=0.9),
            DraftIngredient(name="butter", quantity=2, unit="tbsp", grams=28, amount_estimated=False, source=source, confidence=0.9),
            DraftIngredient(name="garlic", quantity=3, unit="clove", grams=9, amount_estimated=True, source=source, confidence=0.6),
        ],
    )


def draft_guidance():
    return DraftGuidance(
        steps=[
            DraftStep(
                instruction="Mince the garlic.",
                timer_seconds=None,
                doneness_cue=None,
                safety_note=None,
                equipment_swap=None,
                terms=[DraftTerm(term="mince", definition="Chop very small."), DraftTerm(term="fold", definition="x")],
                video_start_seconds=2,
                video_end_seconds=6,
            ),
            DraftStep(
                instruction="Simmer the rice.",
                timer_seconds=900,
                doneness_cue="The water is gone.",
                safety_note=None,
                equipment_swap=None,
                terms=[],
                video_start_seconds=6,
                video_end_seconds=40,
            ),
        ]
    )


def draft_estimates():
    return DraftEstimates(
        items=[
            DraftEstimate(ingredient_id="rice", product_name="Rice, 2 lb", package_size_grams=907, package_price=2.49, calories=240, protein_g=4, carbs_g=53, fat_g=0.4),
            DraftEstimate(ingredient_id="butter", product_name="Butter, 4 sticks", package_size_grams=454, package_price=4.99, calories=200, protein_g=0, carbs_g=0, fat_g=23),
            DraftEstimate(ingredient_id="garlic", product_name="Garlic Bulb", package_size_grams=50, package_price=0.79, calories=13, protein_g=0.6, carbs_g=3, fat_g=0),
            DraftEstimate(ingredient_id="not-in-recipe", product_name="?", package_size_grams=1, package_price=1, calories=999, protein_g=0, carbs_g=0, fat_g=0),
        ]
    )


@pytest.fixture
def fakes(monkeypatch):
    """Fake services; tests tweak `state` to change what they return."""
    state = {"caption": "Garlic butter rice! 1 cup rice, 2 tbsp butter, 3 cloves garlic", "complete": True, "is_recipe": True}
    calls = {"download": 0, "structure_prompts": []}

    def fake_ask(*, system, prompt, output, **_):
        if output is DraftRecipe:
            calls["structure_prompts"].append(prompt)
            source = "transcript" if "<transcript>" in prompt else "caption"
            draft = draft_recipe(complete=state["complete"], source=source)
            if not state["is_recipe"]:
                draft = draft.model_copy(update={"is_recipe": False, "ingredients": []})
            return draft
        if output is DraftGuidance:
            return draft_guidance()
        if output is DraftEstimates:
            return draft_estimates()
        raise AssertionError(output)

    def fake_download(url, workdir):
        calls["download"] += 1
        path = workdir / "video.mp4"
        path.write_bytes(b"")
        return path

    monkeypatch.setattr(claude, "ask", fake_ask)
    monkeypatch.setattr(
        video,
        "fetch_metadata",
        lambda url: video.VideoInfo(url=url, title="Rice", description=state["caption"], uploader="cook", duration=45.0),
    )
    monkeypatch.setattr(video, "download", fake_download)
    monkeypatch.setattr(transcribe, "transcribe", lambda media: [Segment(0, 5, "add three cloves of garlic")])
    monkeypatch.setenv("PIPELINE_MODE", "real")
    return state, calls


def wait(store, job_id):
    for _ in range(200):
        job = store.get_job(job_id)
        if job.status != JobStatus.running:
            return job
        time.sleep(0.01)
    raise AssertionError("job didn't finish")


def test_complete_caption_skips_audio(fakes):
    _, calls = fakes
    store = Store()
    job = wait(store, store.create_job(url=URL, text=None).job_id)

    assert job.status == JobStatus.done
    assert job.stages == ["metadata", "merge"]
    assert calls["download"] == 0

    extraction = store.get_extraction(job.recipe_id)
    assert [i.id for i in extraction.recipe.ingredients] == ["rice", "butter", "garlic"]
    assert extraction.recipe.servings == Servings(value=2, estimated=True)
    # No transcript, so no video timing.
    assert all(s.video_start_seconds is None for s in extraction.steps)


def test_incomplete_caption_transcribes_and_keeps_timing(fakes):
    state, calls = fakes
    state["complete"] = False
    store = Store()
    job = wait(store, store.create_job(url=URL, text=None).job_id)

    assert job.status == JobStatus.done
    assert job.completed_stages == ["metadata", "audio", "merge"]
    assert calls["download"] == 1
    assert "<transcript>" in calls["structure_prompts"][-1]

    extraction = store.get_extraction(job.recipe_id)
    assert {i.source for i in extraction.recipe.ingredients} == {"transcript"}
    assert (extraction.steps[0].video_start_seconds, extraction.steps[0].video_end_seconds) == (2, 6)


def test_no_recipe_fails_with_paste_fallback(fakes):
    state, _ = fakes
    state["is_recipe"] = False
    store = Store()
    job = wait(store, store.create_job(url=URL, text=None).job_id)

    assert job.status == JobStatus.failed
    assert "Paste the caption" in job.error


def test_blocked_video_fails_with_friendly_error(fakes, monkeypatch):
    def blocked(url):
        raise video.VideoError("We couldn't get this video. Paste the caption or ingredient list below instead.")

    monkeypatch.setattr(video, "fetch_metadata", blocked)
    store = Store()
    job = wait(store, store.create_job(url=URL, text=None).job_id)
    assert job.status == JobStatus.failed
    assert job.stage == "metadata"
    assert "Paste the caption" in job.error


def test_pasted_text_runs_merge_only(fakes):
    _, calls = fakes
    store = Store()
    job = wait(store, store.create_job(url=None, text="1 cup rice, 2 tbsp butter").job_id)
    assert job.status == JobStatus.done
    assert job.stages == ["merge"]
    assert calls["download"] == 0


def test_plan_uses_extracted_products_and_steps(fakes):
    store = Store()
    job = wait(store, store.create_job(url=URL, text=None).job_id)
    extraction = store.get_extraction(job.recipe_id)

    plan = build_plan(extraction, "02139", ["butter"])
    assert [g.ingredient_id for g in plan.grocery_list] == ["rice", "garlic"]
    assert all(g.product.price_type == "estimate" for g in plan.grocery_list)
    assert plan.costs.trip_total == pytest.approx(2.49 + 0.79)
    assert plan.steps == extraction.steps
    assert plan.macros_per_serving.approximate is True


def test_to_steps_cleans_terms_and_bad_timestamps():
    guidance = draft_guidance()
    guidance.steps[1].video_start_seconds = 50  # past the end of a 45s video

    steps = to_steps(guidance, has_timing=True, video_duration=45)
    assert [t.term for t in steps[0].terms] == ["mince"]  # "fold" isn't in the instruction
    assert steps[1].video_start_seconds is None and steps[1].video_end_seconds is None
    assert [s.order for s in steps] == [1, 2]

    assert all(s.video_start_seconds is None for s in to_steps(guidance, has_timing=False, video_duration=45))


def test_estimates_ignore_unknown_ids_and_divide_by_servings():
    recipe = to_recipe(draft_recipe(), recipe_id="r", source_url=None, creator=None)
    products, macros = to_products_and_macros(draft_estimates(), recipe)

    assert set(products) == {"rice", "butter", "garlic"}
    assert macros.calories == pytest.approx((240 + 200 + 13) / 2)
    assert macros.approximate is True


def test_duplicate_ingredient_names_get_unique_ids():
    draft = draft_recipe()
    draft.ingredients.append(draft.ingredients[0].model_copy())
    recipe = to_recipe(draft, recipe_id="r", source_url=None, creator=None)
    assert [i.id for i in recipe.ingredients] == ["rice", "butter", "garlic", "rice-2"]


def test_mode_follows_api_key(monkeypatch):
    monkeypatch.delenv("PIPELINE_MODE", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    assert extract.pipeline_mode() == "stub"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    assert extract.pipeline_mode() == "real"
