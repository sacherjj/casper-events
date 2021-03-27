from event_stream_reader import EventStreamSimulator, EventStreamReader
from pathlib import Path
import json
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent.absolute()
DATA_PATH = SCRIPT_DIR / "delta-11_event_stream_16280"


esr = EventStreamReader("http://18.220.220.20:9999/events")
message = defaultdict(int)
for msg in esr.messages():
    if msg.id is None:
        continue
    data = json.loads(msg.data)
    message[list(data.keys())[0]] += 1
    print(msg.data)

# FinalitySignature - block_hash, era_id, signature, public_key
# DeployProcessed - deploy_hash, account, timestamp, ttl, dependencies, block_hash, execution_results
# BlockAdded - block_hash - block:header:era_id - block:header:height
