"""Project-root-relative path resolution.

Resolves paths from the package directory rather than the current working
directory, so the application can be run as `python -m ats` from anywhere.
"""
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent       # src/ats/
SRC_DIR = PACKAGE_DIR.parent                        # src/
PROJECT_ROOT = SRC_DIR.parent                       # repo root

ENV_FILE = PROJECT_ROOT / ".env"
DEFAULT_ENV_FILE = PROJECT_ROOT / "default.env"
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "Data"
DASHBOARD_LAYOUT_CONFIG = DATA_DIR / "dashboard_layout_config.json"
