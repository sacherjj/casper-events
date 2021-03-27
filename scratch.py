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


#{"FinalitySignature":
finality_signature = {
    "block_hash": "fcc5e8f8672f44f3531c2a0498aefd0397c2bcbc4660a7542e04431617ff749d",
    "era_id": 67,
    "signature": "0103290c2676c4c7650c455f04e8aba49ae8e1f21888096778a297095b224656ca982e41e94dd9e92bd3fbe74644fd673ad339c5b475b4203b54ef354f33c67e04",
    "public_key": "01b99d5f54a5147ee34f472d546d84037007025df5e1a13cfdca7aac05e9ac5858"
}

#{"BlockAdded":
block_added_simple = {
    "block_hash": "fcc5e8f8672f44f3531c2a0498aefd0397c2bcbc4660a7542e04431617ff749d",
    "block": {
        "hash": "fcc5e8f8672f44f3531c2a0498aefd0397c2bcbc4660a7542e04431617ff749d",
        "header": {
            "parent_hash": "aaabab07e1e1bec088816d1daad3ab1258620a78ac850f59686e68e728607818",
            "state_root_hash": "ab3bac744d8e66e94833fb1cc02022b7bcd2e9d7c0a08bfee75b986178579da9",
            "body_hash": "1ec06dc14160360211f445bde8d75b925e079a9812bfbfd790544e56106e9e9e",
            "random_bit": false,
            "accumulated_seed": "9d9db08b7f38d5ce4ef0dfd998ff3d4acb6537b4e9b7563948882c6f44a899c3",
            "era_end": null,  # Huge JSON structure
            "timestamp": "2021-03-22T13:11:41.312Z",
            "era_id": 67,
            "height": 16495,
            "protocol_version": "1.0.2"
        },
        "body": {
            "proposer": "013f774a58f4d40bd9b6cce7e306e53646913860ef2a111d00f0fe7794010c4012",
            "deploy_hashes": ["e0cce91995356312402c525d9af34aa063395868281e6775498297a91280de99","558eeb213af94495765cbf05aee26589d9ec4a7f3a4fb5680fa23a2ba8ecd22e"],
            "transfer_hashes": []
        }
    }
}

# {"DeployProcessed":
deploy_processed = {
    "deploy_hash": "558eeb213af94495765cbf05aee26589d9ec4a7f3a4fb5680fa23a2ba8ecd22e",
    "account": "01054c929d687267a30341c759b4a9cab1238cb2de65546be43dad479c50745724",
    "timestamp": "2021-03-22T12:59:47.939Z",
    "ttl": "1h",
    "dependencies": [],
    "block_hash": "fcc5e8f8672f44f3531c2a0498aefd0397c2bcbc4660a7542e04431617ff749d",
    # execution results is JSON struct
    "execution_result": {"Failure": {"effect":{"operations":[{"key":"hash-8e0e6159a62a833ec19b4b3ba9b6d19e621797d5c9ccef797a5a2cde9cc49f1e","kind":"Read"},{"key":"balance-822e9b743929b8e696fcba90237dcf382a661111a3d207ff1a4709e389ff5fec","kind":"Write"},{"key":"balance-9f6c37b45d114cdc7b0c532f4ca8c18eeec8e9603ebc39eb01f59152007eea49","kind":"Read"},{"key":"balance-5721022e571d87b10aa8c42f1f193605bce249e5b37ffa14de9bf18eff1658e2","kind":"Write"},{"key":"hash-a410b5562ad8385573adcd8241b24358922ac694e789e2c220eac7135be6e4eb","kind":"Read"}],"transforms":[{"key":"balance-5721022e571d87b10aa8c42f1f193605bce249e5b37ffa14de9bf18eff1658e2","transform":{"WriteCLValue":{"cl_type":"U512","bytes":"08e0a8ba37d9a7ad50","parsed":"5813487245389900000"}}},{"key":"hash-8e0e6159a62a833ec19b4b3ba9b6d19e621797d5c9ccef797a5a2cde9cc49f1e","transform":"Identity"},{"key":"hash-a410b5562ad8385573adcd8241b24358922ac694e789e2c220eac7135be6e4eb","transform":"Identity"},{"key":"balance-9f6c37b45d114cdc7b0c532f4ca8c18eeec8e9603ebc39eb01f59152007eea49","transform":"Identity"},{"key":"balance-822e9b743929b8e696fcba90237dcf382a661111a3d207ff1a4709e389ff5fec","transform":{"AddUInt512":"100000000000"}}]},"transfers":[],"cost":"11406830","error_message":"User error: 1"}}
}

