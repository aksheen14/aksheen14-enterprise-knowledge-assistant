import os
import sys
import pytest
from dotenv import load_dotenv


# 1. PATH RESOLUTION
# This ensures Pytest can find your backend folder, even though tests/ is outside of it.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 2. THE VAULT LOCK
# We MUST load the test environment variables BEFORE importing anything from your app.
# This guarantees your app uses the local CHROMA_PATH and doesn't touch Railway.
test_env_path = os.path.join(BACKEND_DIR, ".env.test")

# --- ADD THESE TWO LINES ---
print(f"\n[DEBUG] Looking for test env at: {test_env_path}")
print(f"[DEBUG] Does the file actually exist? {os.path.exists(test_env_path)}")
# ---------------------------

load_dotenv(test_env_path, override=True)

from backend.main import app

# 3. IMPORT THE APP
# Now that the environment is safe, it is safe to import your Flask app.
from backend.main import app  

# 4. THE TEST CLIENT FIXTURE
# This creates a "fake" web browser that can send requests to your routes
# without actually needing to spin up a live server on port 8080.
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client