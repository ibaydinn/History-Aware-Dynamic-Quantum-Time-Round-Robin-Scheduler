"""Command-line entry point; all calculations live in the metrics package."""

from pathlib import Path
import sys

# Support invoking this script directly from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metrics.cli import main

if __name__ == "__main__":
    main()
