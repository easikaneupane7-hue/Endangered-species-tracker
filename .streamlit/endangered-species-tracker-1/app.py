from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import app  # noqa: F401
