"""Write the API's OpenAPI schema to backend/openapi.json.

The frontend generates its TypeScript types from this file (`npm run gen:api`
in frontend/), so rerun this whenever app/models.py or the routes change.
"""

import json
from pathlib import Path

from app.main import app

out = Path(__file__).resolve().parent.parent / "openapi.json"
out.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"Wrote {out}")
