import os
from pathlib import Path

BASE_SERVER = "3.14.161.135"
# BASE_SERVER = "3.136.227.9"
RPC_SERVER_URL = f"http://{BASE_SERVER}:7777/rpc"
SSE_SERVER_MAIN_URL = f"http://{BASE_SERVER}:9999/events/main"
SSE_SERVER_DEPLOYS_URL = f"http://{BASE_SERVER}:9999/events/deploys"
SSE_SERVER_SIGS_URL = f"http://{BASE_SERVER}:9999/events/sigs"

SCRIPT_DIR = Path(__file__).parent.absolute()
DATA_DIR = SCRIPT_DIR / "events"

os.environ['AWS_DEFAULT_REGION'] = 'us-west-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
