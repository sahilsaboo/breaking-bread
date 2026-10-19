"""Estimated prices and macros, until real sources land.

STUB-level data: the grocery price source is still open (docs/decisions.md #1)
and the USDA adapter isn't built, so Claude estimates both. Every price is
tagged "estimate" and every macro total is marked approximate, so the UI never
presents them as exact. Swap this module for the pricing adapter and USDA
lookups when they exist; the rest of the pipeline only sees Products and Macros.
"""

import json
import logging

from pydantic import BaseModel, Field

from app.adapters import claude
from app.models import Macros, Product, Recipe

log = logging.getLogger(__name__)

STORE_ID = "estimate"
STORE_NAME = "Estimated prices"


class DraftEstimate(BaseModel):
    ingredient_id: str
    product_name: str = Field(description="What to buy, with package size, e.g. 'Garlic Bulb' or 'Heavy Cream, 1 pint'")
    package_size_grams: float = Field(description="Weight of one package in grams")
    package_price: float = Field(description="Typical US supermarket price in USD for one package")
    calories: float = Field(description="Calories in the amount used in the recipe (not the whole package)")
    protein_g: float
    carbs_g: float
    fat_g: float


class DraftEstimates(BaseModel):
    items: list[DraftEstimate]


SYSTEM = """You estimate grocery costs and nutrition for a recipe.

For each ingredient (by its id):
- Pick the product a budget-minded student would buy at a typical US supermarket: store brand,
  the smallest common package that covers the amount used. Pantry staples (salt, oil, spices)
  come in their usual smallest package.
- Give that package's weight in grams and a typical current price in USD.
- Give calories, protein, carbs, and fat for the amount used in the recipe (the grams given),
  using standard nutrition values for that food.

Return exactly one item per ingredient id."""


def estimate(recipe: Recipe) -> tuple[dict[str, Product], Macros]:
    ingredients = [{"id": i.id, "name": i.name, "grams_used": i.grams} for i in recipe.ingredients]
    draft = claude.ask(
        system=SYSTEM,
        prompt=f"<ingredients>\n{json.dumps(ingredients, ensure_ascii=False)}\n</ingredients>",
        output=DraftEstimates,
        effort="low",
    )
    return to_products_and_macros(draft, recipe)


def to_products_and_macros(draft: DraftEstimates, recipe: Recipe) -> tuple[dict[str, Product], Macros]:
    known = {i.id for i in recipe.ingredients}
    products: dict[str, Product] = {}
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}

    for item in draft.items:
        if item.ingredient_id not in known or item.ingredient_id in products:
            continue
        if item.package_size_grams > 0 and item.package_price >= 0:
            products[item.ingredient_id] = Product(
                store_id=STORE_ID,
                store_name=STORE_NAME,
                product_name=item.product_name,
                package_size_grams=item.package_size_grams,
                package_price=round(item.package_price, 2),
                price_type="estimate",
            )
        for key in totals:
            totals[key] += max(getattr(item, key), 0.0)

    missing = known - products.keys()
    if missing:
        log.warning("No price estimate for %s", sorted(missing))

    # Whole-recipe totals; planning divides them by servings alongside the cost.
    return products, Macros(**totals, approximate=True)
