import os
from pathlib import Path

SSE_SERVER_URL = "http://18.220.220.20:9999/events"
SCRIPT_DIR = Path(__file__).parent.absolute()
DATA_DIR = SCRIPT_DIR / "events"

os.environ['AWS_DEFAULT_REGION'] = 'us-west-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
