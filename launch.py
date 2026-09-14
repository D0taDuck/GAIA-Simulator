"""Runs from a normal Python installation or the local environment built for Gaia."""
from pathlib import Path
import os
import sys

os.chdir(Path(__file__).resolve().parent)
from gaia.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["serve"]))
