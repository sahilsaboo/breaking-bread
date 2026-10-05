import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.jobs import store
from app.models import CreateRecipeRequest, Job, MealPlan, PlanRequest, Recipe
from app.pipeline.extract import InvalidLinkError, validate_link
from app.pipeline.plan import UnknownIngredientError, build_plan

app = FastAPI(
    title="Breaking Bread API",
    description="Pasted TikTok/Reel link -> recipe -> grocery list, cost, macros, and guidance.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/recipes", status_code=202)
def create_recipe(body: CreateRecipeRequest) -> Job:
    """Start extraction from a link or pasted text. Poll the returned job."""
    url = None
    if body.url:
        try:
            url = validate_link(body.url)
        except InvalidLinkError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
    return store.create_job(url=url, text=body.text)


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> Job:
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@app.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str) -> Recipe:
    recipe = store.get_recipe(recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return recipe


@app.post("/recipes/{recipe_id}/plan")
def plan_recipe(recipe_id: str, body: PlanRequest) -> MealPlan:
    recipe = store.get_recipe(recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    try:
        return build_plan(recipe, body.zip_code, body.owned_ingredient_ids)
    except UnknownIngredientError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
