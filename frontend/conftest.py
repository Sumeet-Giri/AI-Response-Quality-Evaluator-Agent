"""
Ensures `frontend/` itself is on sys.path when pytest runs, so
`from pages_content import ...` / `from utils import ...` / `from
components import ...` resolve the same way they do when Streamlit runs
app.py directly -- regardless of the exact directory pytest is invoked
from.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
