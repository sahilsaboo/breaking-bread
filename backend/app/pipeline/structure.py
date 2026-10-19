"""Merge step: turn caption / transcript / pasted text into a structured recipe."""

import re
from typing import Literal

from pydantic import BaseModel, Field

from app.adapters import claude
from app.models import Ingredient, Recipe, Servings

# Last-resort fallback if Claude returns no usable serving count.
DEFAULT_SERVINGS = 2


class DraftIngredient(BaseModel):
    name: str = Field(description="Plain grocery name, lowercase, e.g. 'garlic', 'heavy cream'")
    quantity: float | None = Field(description="Amount as stated, e.g. 2 for '2 cloves'; null if not stated")
    unit: str | None = Field(description="Unit as stated, e.g. 'clove', 'cup', 'g'; null for countable items")
    grams: float = Field(description="Best estimate of the weight used, in grams")
    amount_estimated: bool = Field(description="True if the source didn't state the amount and you estimated it")
    source: Literal["caption", "transcript", "pasted"] = Field(description="Where this ingredient was found")
    confidence: float = Field(description="0-1: how sure you are this ingredient and amount are right")


class DraftRecipe(BaseModel):
    is_recipe: bool = Field(description="False if the sources don't describe a dish to cook")
    title: str = Field(description="Short dish name, e.g. 'Creamy Garlic Chicken Pasta'")
    servings: int = Field(
        description="How many servings the recipe makes: the stated count, else your best estimate from the amounts"
    )
    servings_stated: bool = Field(
        description="True if the sources say how many it serves or makes; false if you estimated it"
    )
    ingredients: list[DraftIngredient]
    complete: bool = Field(
        description="True if the sources name every ingredient the dish needs, with amounts for most of them"
    )


SYSTEM = """You turn cooking videos into recipes for college students who are new to cooking.

You get the video's caption and/or a transcript of what the cook says, or text the user pasted.
Return the dish and its ingredient list.

Rules:
- Only include ingredients that the sources actually mention. Never add ingredients that
  "usually" go in the dish. If the cook says "season it" without naming seasonings, don't
  add any.
- Use plain grocery names a beginner would look for in a store.
- Combine duplicates (garlic mentioned twice is one ingredient with the total amount).
- Always estimate grams for the amount used. If the amount isn't stated, estimate a typical
  amount for this recipe and set amount_estimated to true.
- Lower the confidence when the transcript is unclear or the amount is a guess.
- Servings: if the sources say how many it serves or makes ("serves 4", "makes 6 tacos",
  "dinner for two", "4 meal-prep containers"), use that and set servings_stated to true.
  Otherwise estimate how many normal adult portions the ingredient amounts make (for example
  1 lb pasta with sauce is about 4) and set servings_stated to false.
- Set complete to false when the sources seem to leave ingredients out (for example a caption
  that only says "recipe below" or names the dish without a list).
- If the sources don't describe a dish (no ingredients at all), set is_recipe to false
  and return an empty ingredient list."""


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "ingredient"


def _unique_ids(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    ids = []
    for name in names:
        base = _slug(name)
        seen[base] = seen.get(base, 0) + 1
        ids.append(base if seen[base] == 1 else f"{base}-{seen[base]}")
    return ids


def build_prompt(*, title: str | None, caption: str | None, transcript: str | None, pasted: str | None) -> str:
    parts = []
    if title:
        parts.append(f"<video_title>\n{title}\n</video_title>")
    if caption:
        parts.append(f"<caption>\n{caption}\n</caption>")
    if transcript:
        parts.append(f"<transcript>\n{transcript}\n</transcript>")
    if pasted:
        parts.append(f"<pasted_text>\n{pasted}\n</pasted_text>")
    return "\n\n".join(parts)


def structure_recipe(
    *,
    recipe_id: str,
    source_url: str | None,
    creator: str | None = None,
    title: str | None = None,
    caption: str | None = None,
    transcript: str | None = None,
    pasted: str | None = None,
) -> tuple[DraftRecipe, Recipe]:
    draft = claude.ask(
        system=SYSTEM,
        prompt=build_prompt(title=title, caption=caption, transcript=transcript, pasted=pasted),
        output=DraftRecipe,
        effort="medium",
    )
    return draft, to_recipe(draft, recipe_id=recipe_id, source_url=source_url, creator=creator)


def to_recipe(draft: DraftRecipe, *, recipe_id: str, source_url: str | None, creator: str | None) -> Recipe:
    ids = _unique_ids([i.name for i in draft.ingredients])
    ingredients = [
        Ingredient(
            id=ingredient_id,
            name=i.name.strip(),
            quantity=i.quantity,
            unit=i.unit,
            grams=i.grams if i.grams > 0 else None,
            estimated=i.amount_estimated,
            source=i.source,
            confidence=min(max(i.confidence, 0.0), 1.0),
        )
        for ingredient_id, i in zip(ids, draft.ingredients)
    ]
    servings = (
        Servings(value=draft.servings, estimated=not draft.servings_stated)
        if draft.servings > 0
        else Servings(value=DEFAULT_SERVINGS, estimated=True)
    )
    return Recipe(
        id=recipe_id,
        source_url=source_url,
        title=draft.title.strip() or "Your recipe",
        creator=creator,
        servings=servings,
        ingredients=ingredients,
    )
