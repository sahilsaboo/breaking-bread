import json
from functools import cache
from importlib import resources


@cache
def sample() -> dict:
    """The sample recipe used by every stub until real stages replace them."""
    return json.loads(resources.files("app.fixtures").joinpath("sample_recipe.json").read_text(encoding="utf-8"))
