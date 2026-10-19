import os
import tempfile

# Tests never call Claude or TikTok, even when backend/.env has a real key:
# load_dotenv() doesn't override variables that are already set.
os.environ["PIPELINE_MODE"] = "stub"
# Tests must not read or fill the real extraction cache, or write to the real usage log.
os.environ["EXTRACTION_CACHE"] = "off"
os.environ["USAGE_LOG"] = os.path.join(tempfile.gettempdir(), "breaking-bread-test-usage.jsonl")
