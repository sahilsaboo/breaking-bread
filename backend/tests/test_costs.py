from app.costs import compute_costs, packages_needed, to_cents
from app.models import Ingredient, Product


def ingredient(grams, package_grams, price, owned=False):
    return Ingredient(
        id="x",
        name="x",
        grams=grams,
        estimated=False,
        source="caption",
        confidence=1,
        owned=owned,
        product=Product(
            store_id="s",
            store_name="s",
            product_name="p",
            package_size_grams=package_grams,
            package_price=price,
            price_type="estimate",
        ),
    )


def test_packages_needed_rounds_up_and_buys_at_least_one():
    assert packages_needed(ingredient(9, 50, 0.79)) == 1
    assert packages_needed(ingredient(50, 50, 0.79)) == 1
    assert packages_needed(ingredient(51, 50, 0.79)) == 2
    assert packages_needed(ingredient(None, 50, 0.79)) == 1


def test_trip_total_skips_owned_items():
    items = [ingredient(9, 50, 0.79), ingredient(28, 454, 4.99, owned=True)]
    assert compute_costs(items, servings=2).trip_total == 0.79


def test_per_meal_counts_owned_items_by_amount_used():
    # garlic: 9/50 * 0.79 = 0.1422; butter: 28/454 * 4.99 = 0.30776 -> 0.44995 / 2
    items = [ingredient(9, 50, 0.79), ingredient(28, 454, 4.99, owned=True)]
    assert compute_costs(items, servings=2).per_meal == 0.22


def test_money_rounds_half_up():
    assert to_cents(0.225) == 0.23
    assert to_cents(0.224) == 0.22


def test_costs_are_always_approximate():
    assert compute_costs([], servings=1).approximate is True
