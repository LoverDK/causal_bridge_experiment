"""Run the current-method unit tests with the package root configured."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT)
raise SystemExit(result.returncode)
