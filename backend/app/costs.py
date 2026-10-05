"""Cost rules from docs/technical-spec.md.

Trip cost: what you'll spend at the store, i.e. full packages for items not owned.
Per-meal cost: what one serving actually uses, counting owned items too.
"""

import math
from decimal import ROUND_HALF_UP, Decimal

from app.models import Costs, Ingredient


def to_cents(amount: float) -> float:
    """Round money half-up to cents (plain round() gives round(0.225, 2) == 0.22)."""
    return float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def packages_needed(ingredient: Ingredient) -> int:
    """Smallest number of packages that covers the amount used (at least one)."""
    if ingredient.product is None:
        return 0
    if ingredient.grams is None:
        return 1
    return max(1, math.ceil(ingredient.grams / ingredient.product.package_size_grams))


def trip_total(ingredients: list[Ingredient]) -> float:
    return to_cents(
        sum(
            packages_needed(i) * i.product.package_price
            for i in ingredients
            if i.product is not None and not i.owned
        )
    )


def per_meal(ingredients: list[Ingredient], servings: int) -> float:
    used = sum(
        i.grams / i.product.package_size_grams * i.product.package_price
        for i in ingredients
        if i.product is not None and i.grams is not None
    )
    return to_cents(used / servings)


def compute_costs(ingredients: list[Ingredient], servings: int) -> Costs:
    return Costs(trip_total=trip_total(ingredients), per_meal=per_meal(ingredients, servings))
