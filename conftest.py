import sys
from pathlib import Path

# Make the repository root importable so `import wave` works when running
# pytest from any directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
