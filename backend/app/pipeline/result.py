from dataclasses import dataclass

from app.models import Macros, Product, Recipe, Step


@dataclass
class Extraction:
    """Everything the pipeline learns about one recipe before planning.

    Steps, products, and macros don't depend on the user's ZIP code or what
    they own, so they're produced once here; planning only does the math.
    """

    recipe: Recipe
    steps: list[Step]
    products: dict[str, Product]  # by ingredient id
    macros_per_serving: Macros
