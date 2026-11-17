import os
import sys
from pathlib import Path

# Tests run offline: switch off telemetry export from the local hosting server.
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
