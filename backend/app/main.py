import os

from dotenv import load_dotenv

# Load backend/.env (API keys, settings) before anything reads the environment.
# .env wins over the shell, which may set ANTHROPIC_BASE_URL for its own use.
# Render has no .env file, so its dashboard variables still apply there.
load_dotenv(override=True)

from fastapi import APIRouter, FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.jobs import store  # noqa: E402
from app.models import CreateRecipeRequest, Job, MealPlan, PlanRequest, Recipe  # noqa: E402
from app.pipeline.extract import InvalidLinkError, validate_link  # noqa: E402
from app.pipeline.plan import UnknownIngredientError, build_plan  # noqa: E402

app = FastAPI(
    title="Breaking Bread API",
    description="Pasted TikTok/Reel link -> recipe -> grocery list, cost, macros, and guidance.",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Every route lives under /api so the paths match in local dev and production,
# where the frontend's domain forwards /api/* to this service.
router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/recipes", status_code=202)
def create_recipe(body: CreateRecipeRequest) -> Job:
    """Start extraction from a link or pasted text. Poll the returned job."""
    url = None
    if body.url:
        try:
            url = validate_link(body.url)
        except InvalidLinkError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
    return store.create_job(url=url, text=body.text)


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> Job:
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str) -> Recipe:
    recipe = store.get_recipe(recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return recipe


@router.post("/recipes/{recipe_id}/plan")
def plan_recipe(recipe_id: str, body: PlanRequest) -> MealPlan:
    extraction = store.get_extraction(recipe_id)
    if extraction is None:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    try:
        return build_plan(extraction, body.zip_code, body.owned_ingredient_ids)
    except UnknownIngredientError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


app.include_router(router)

# Temporary: hosting spike for decision #13. Only exists when SPIKE_TOKEN is set.
if os.environ.get("SPIKE_TOKEN"):
    from app.spike_routes import router as spike_router

    app.include_router(spike_router)
