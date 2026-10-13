import os

import dotenv

# Tests never call Claude or TikTok, even when backend/.env has a real key.
# app.main loads .env with override=True, so skip loading it entirely in tests.
dotenv.load_dotenv = lambda *args, **kwargs: False
os.environ["PIPELINE_MODE"] = "stub"
