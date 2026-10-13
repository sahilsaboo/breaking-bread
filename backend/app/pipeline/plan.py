"""Turn an extraction into the results page for one ZIP code and pantry.

Steps, products, and macros were produced during extraction; this step only
applies what the user owns and does the cost math. Prices are estimates until
the pricing source is chosen (docs/decisions.md #1), so the ZIP code isn't
used for lookups yet.
"""

from app.costs import compute_costs, packages_needed, to_cents
from app.models import GroceryItem, MealPlan
from app.pipeline.result import Extraction


class UnknownIngredientError(ValueError):
    pass


def build_plan(extraction: Extraction, zip_code: str, owned_ids: list[str]) -> MealPlan:
    recipe = extraction.recipe
    known = {i.id for i in recipe.ingredients}
    unknown = set(owned_ids) - known
    if unknown:
        raise UnknownIngredientError(f"Unknown ingredient ids: {sorted(unknown)}")

    ingredients = [
        i.model_copy(update={"owned": i.id in owned_ids, "product": extraction.products.get(i.id)})
        for i in recipe.ingredients
    ]
    grocery_list = [
        GroceryItem(
            ingredient_id=i.id,
            name=i.name,
            product=i.product,
            packages=packages_needed(i),
            line_total=to_cents(packages_needed(i) * i.product.package_price),
        )
        for i in ingredients
        if not i.owned and i.product is not None
    ]

    return MealPlan(
        recipe_id=recipe.id,
        source_url=recipe.source_url,
        title=recipe.title,
        zip_code=zip_code,
        servings=recipe.servings,
        ingredients=ingredients,
        grocery_list=grocery_list,
        steps=extraction.steps,
        costs=compute_costs(ingredients, recipe.servings.value),
        macros_per_serving=extraction.macros_per_serving,
    )
