from event_stream_reader import EventStreamReader
from config import DATA_DIR, SSE_SERVER_URL
from message_structure import MessageData

esr = EventStreamReader(SSE_SERVER_URL)

# Three message types:
# DeployProcessed - Has no era_id, can store in block-hash folder and move into era_id folder when we get BlockAdded
#   filename - "deploy-<deploy_hash>"
# BlockAdded - Has era_id, can store in era_id folder
#   filename - "block-<block_hash>"
# FinalitySignature = Has era_id, can store in era_id folder
#   filename = "finsig-<block_hash>-<public_key>

for msg in esr.messages():
    if not msg:
        continue
    data = MessageData.from_json(msg.data)
    pk = data.primary_key
    era_id = data.era_id
    directory = f"era-{era_id}" if not data.is_deploy else f"block-{data.block_hash}"
    # Deploys are made into block-<block_hash> directory that needs to be moved once BlockAdded test is what era the
    # Block was in.

    print(data)
