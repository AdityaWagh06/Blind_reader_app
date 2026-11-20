import sys
from pathlib import Path

# let tests import app, config and utils from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
