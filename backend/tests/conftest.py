import os

# Tests never call Claude or TikTok, even when backend/.env has a real key:
# load_dotenv() doesn't override variables that are already set.
os.environ["PIPELINE_MODE"] = "stub"
