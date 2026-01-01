"""Local development helper script."""

import sys
from pathlib import Path

# Add src to path (go up one level to project root, then into src)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jobs.main import main


if __name__ == "__main__":
    main()
