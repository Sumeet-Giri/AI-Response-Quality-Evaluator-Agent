from pathlib import Path

# Base directory (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Reserved for a future file/document upload endpoint (Milestone 1 originally
# scoped an "optional source document" input; the endpoint that used to
# reference this, app/api/routes.py, was removed as dead/broken code during
# the architecture cleanup -- see the backend architecture review). Kept
# here, not deleted, since this is genuine forward-looking config, not
# unused code with no future purpose.
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(exist_ok=True)