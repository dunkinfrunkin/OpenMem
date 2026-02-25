import sys
from pathlib import Path

# Auto-discover the openmem package from the repo's src/ directory
# so the benchmark works without `pip install -e .`
_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
