"""Turn an extracted recipe into the results page.

STUB: prices, guidance, and macros come from the sample fixture. The real
version calls the pricing adapter, USDA, and Claude.
"""

from app.costs import compute_costs, packages_needed, to_cents
from app.models import GroceryItem, Macros, MealPlan, Product, Recipe, Step
from app.pipeline.fixtures import sample

STUB_STORE_ID = "stub"
STUB_STORE_NAME = "Estimated prices"


class UnknownIngredientError(ValueError):
    pass


def _stub_product(ingredient_id: str) -> Product | None:
    product = sample()["products"].get(ingredient_id)
    if product is None:
        return None
    return Product(
        store_id=STUB_STORE_ID,
        store_name=STUB_STORE_NAME,
        price_type="estimate",
        **product,
    )


def build_plan(recipe: Recipe, zip_code: str, owned_ids: list[str]) -> MealPlan:
    known = {i.id for i in recipe.ingredients}
    unknown = set(owned_ids) - known
    if unknown:
        raise UnknownIngredientError(f"Unknown ingredient ids: {sorted(unknown)}")

    ingredients = [
        i.model_copy(update={"owned": i.id in owned_ids, "product": _stub_product(i.id)})
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
    approximate = recipe.servings.estimated or any(i.estimated for i in ingredients)

    return MealPlan(
        recipe_id=recipe.id,
        source_url=recipe.source_url,
        title=recipe.title,
        zip_code=zip_code,
        servings=recipe.servings,
        ingredients=ingredients,
        grocery_list=grocery_list,
        steps=[Step.model_validate(s) for s in sample()["steps"]],
        costs=compute_costs(ingredients, recipe.servings.value),
        macros_per_serving=Macros(**sample()["macros_per_serving"], approximate=approximate),
    )
