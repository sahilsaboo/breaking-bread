"""Shared data contract for the whole pipeline.

These models mirror the schema in docs/technical-spec.md. The frontend's
TypeScript types are generated from the OpenAPI output of these models
(`npm run gen:api` in frontend/), so change them here first.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

IngredientSource = Literal["caption", "transcript", "frames", "pasted", "inferred"]
PriceType = Literal["store price", "estimate"]


class Servings(BaseModel):
    value: int = Field(gt=0)
    estimated: bool


class Product(BaseModel):
    store_id: str
    store_name: str
    product_name: str
    package_size_grams: float = Field(gt=0)
    package_price: float = Field(ge=0)
    price_type: PriceType


class Ingredient(BaseModel):
    id: str
    name: str
    quantity: float | None = None
    unit: str | None = None
    grams: float | None = None
    estimated: bool
    source: IngredientSource
    confidence: float = Field(ge=0, le=1)
    owned: bool = False
    product: Product | None = None
    fdc_id: int | None = None


class Term(BaseModel):
    term: str
    definition: str


class Step(BaseModel):
    order: int
    instruction: str
    timer_seconds: int | None = None
    doneness_cue: str | None = None
    safety_note: str | None = None
    equipment_swap: str | None = None
    terms: list[Term] = []


class Costs(BaseModel):
    trip_total: float
    per_meal: float
    currency: Literal["USD"] = "USD"
    approximate: Literal[True] = True


class Macros(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    approximate: bool


class Recipe(BaseModel):
    """Output of extraction: what the reel says to cook."""

    id: str
    source_url: str | None
    title: str
    creator: str | None = None
    servings: Servings
    ingredients: list[Ingredient]


class GroceryItem(BaseModel):
    ingredient_id: str
    name: str
    product: Product
    packages: int = Field(gt=0, description="How many packages to buy")
    line_total: float = Field(description="packages x package_price")


class MealPlan(BaseModel):
    """Output of planning: the full results page for one recipe."""

    recipe_id: str
    source_url: str | None
    title: str
    zip_code: str
    servings: Servings
    ingredients: list[Ingredient]
    grocery_list: list[GroceryItem]
    steps: list[Step]
    costs: Costs
    macros_per_serving: Macros


# --- Jobs -----------------------------------------------------------------


class Stage(StrEnum):
    """Extraction stages, in the order they run."""

    metadata = "metadata"
    audio = "audio"
    frames = "frames"
    merge = "merge"


class JobStatus(StrEnum):
    running = "running"
    done = "done"
    failed = "failed"


class Job(BaseModel):
    job_id: str
    status: JobStatus
    stages: list[Stage] = Field(description="Stages this job plans to run, in order")
    stage: Stage | None = Field(description="Stage running now, or the one that failed")
    completed_stages: list[Stage]
    recipe_id: str | None = None
    error: str | None = None


# --- Requests -------------------------------------------------------------


class CreateRecipeRequest(BaseModel):
    """Start extraction from a link, or from pasted caption/ingredient text."""

    url: str | None = None
    text: str | None = Field(default=None, max_length=20_000)

    @model_validator(mode="after")
    def exactly_one_input(self) -> "CreateRecipeRequest":
        if bool(self.url) == bool(self.text and self.text.strip()):
            raise ValueError("Provide either a link or pasted text, not both.")
        return self


class PlanRequest(BaseModel):
    zip_code: str = Field(pattern=r"^\d{5}$")
    owned_ingredient_ids: list[str] = []
