"""Quickstart entrypoint: `python monitoring.py --mode simulate|ingest`.

The real implementation lives in the installable `environmental_monitoring`
package (`pip install -e .`); this thin script exists so the quickstart
command works even without an editable install, by adding `src/` to the
path. Prefer the `envmon` console script or `python -m environmental_monitoring.cli`
once the package is installed.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from environmental_monitoring.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
