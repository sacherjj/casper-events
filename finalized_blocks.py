from sseclient import SSEClient
import requests

from time import sleep
from collections import defaultdict
import json

# This script is a full stand-alone example of detecting when blocks have been finalized and are irreversible.
# Required python3 packages: requests, sseclient
#
# A block is proposed and then validating nodes provide a finality signature as their indication
# that the block is final.
#
# A block is finalized when 67% of the validator weight have finalized the block.
# Detecting this requires keeping track of
#  - current validator list and weights
#  - finality signatures for a block
#
# This example uses the SSE event stream from a node as this is event driven, provides the fastest response, and
# eliminates polling of an RPC call.
#
# At startup, the validators weights is not known for the current Era, so this is retrieved via RPC calls.  This
# should be the only RPC calls needed and all further validator weights are taken from the switch block (last block) of
# the Era that comes in through the event stream.
#

BASE_SERVER = "3.14.161.135"
RPC_SERVER_URL = f"http://{BASE_SERVER}:7777/rpc"
SSE_SERVER_URL = f"http://{BASE_SERVER}:9999/events"


RECONNECT_DELAY_SEC = 5
RECONNECT_COUNT = 1500


def event_stream_messages():
    """
    Blocking method that continuously yields messages from the SSE server.
    """
    reconnect_count = 0
    while reconnect_count < RECONNECT_COUNT:
        reconnect_count += 1
        try:
            # On restart we might crawl through a bunch, but this doesn't miss them if it is a server restart.
            for message in SSEClient(f"{SSE_SERVER_URL}?start_from=0"):
                # SSE may send empty messages.  We ignore those.
                if message.id is not None:
                    reconnect_count = 0
                    yield message
            print("Stream ended without error, retrying after delay.")
        except Exception as e:
            print(f"Error occurred: {e}")
        sleep(RECONNECT_DELAY_SEC)
    else:
        print(f"Reconnect count: {RECONNECT_COUNT} exceeded. Exiting...")


class EraData:
    def __init__(self):
        self._era_data = defaultdict(dict)
        # This is the main data structure that could be represented by a database or other store
        # {<era_id>:
        #           "weights": {<validator_key>: <validator_weight>, ...},
        #           "total_weight": <int total of all validator_weights>,
        #           "block_signatures": {"block_hash": [<public_key of validator signature>, ...], ...}
        # }

    @staticmethod
    def _get_block_data_from_rpc(block_hash=None) -> tuple:
        """
        Returns (height, era_id, parent_hash, era_end) from block queried by block_height.
        If no block_height is given it will return the latest block.
        """
        if block_hash:
            params = [{"Hash": block_hash}]
        else:
            params = []

        payload = json.dumps({"jsonrpc": "2.0", "method": "chain_get_block", "params": params, "id": 1})
        headers = {'content-type': "application/json", 'cache-control': "no-cache"}
        try:
            response = requests.request("POST", RPC_SERVER_URL, data=payload, headers=headers)
            json_data = json.loads(response.text)
            block_data = json_data["result"]
            block_header = block_data["block"]["header"]
            return block_header["height"], block_header["era_id"], block_header["parent_hash"], block_header["era_end"]
        except Exception as e:
            print(f"Error during RPC call: {e}")

    def _populate_validator_data_from_rpc(self, era_id: int, block_hash: str) -> None:
        """
        This loads initial validator weight information on startup as we have not received a switch block from the
        event stream yet.

        This should be used sparingly as it is VERY slow compared to just parsing the event stream.
        """
        print(f"Retrieving validator info from RPC for era: {era_id}")
        block_height, cur_era_id, parent_hash, era_end = self._get_block_data_from_rpc(block_hash)

        # Walk the parent hashes back until we get switch block before era_id needed for validator info.
        while cur_era_id == era_id:
            block_height, cur_era_id, parent_hash, era_end = self._get_block_data_from_rpc(parent_hash)

        self._add_era_data(era_id, era_end["next_era_validator_weights"])

    def era_data(self, era_id: int, block_hash: str) -> dict:
        """
        Returns data about that era.  If it does not exist, this is before we populated with
        era_end from the switch block stream, so we retrieve with the RPC.

        After the first switch block, this should not require RPC use.
        """
        if era_id not in self._era_data:
            self._populate_validator_data_from_rpc(era_id, block_hash)
        return self._era_data[era_id]

    def _add_era_data(self, next_era_id: int, next_era_validator_weights: dict) -> None:
        """
        Creates expected self._era_data structures and validator weights for block finalization detection
        """
        weights = {data["validator"]: int(data["weight"]) for data in next_era_validator_weights}
        self._era_data[next_era_id]["weights"] = weights
        self._era_data[next_era_id]["total_weight"] = sum(weights.values())
        self._era_data[next_era_id]["block_weight"] = defaultdict(int)

        # We are pruning data to keep current and next as finalization signatures for the switch block
        # will come in after the switch block is received.
        delete_era = next_era_id - 2
        for key in [key for key in self._era_data if key <= delete_era]:
            print(f"Removing Era data for era_id: {key}")
            del self._era_data[key]

    def process_finality_signature(self, fin_sig: dict) -> bool:
        """
        Processes the finality signature received from the event stream.

        Returns True is block has been finalized after including this signature
        """
        era_id = fin_sig["era_id"]
        block_hash = fin_sig["block_hash"]
        ed = self.era_data(era_id, block_hash)
        signature = fin_sig["signature"]
        # TODO: Validate signature
        validator_key = fin_sig["public_key"]
        validator_weight = ed["weights"].get(validator_key, 0) 
        ed["block_weight"][block_hash] += validator_weight
        weight_ratio = ed["block_weight"][block_hash] / ed["total_weight"]
        return weight_ratio > 0.67

    def process_block(self, block: dict) -> None:
        """
        This will be called with each block received.  If the block has era_end data, this will be used to update
        next era_id's validator weight.
        """
        block_hash = block["block_hash"]
        era_id = block["block"]["header"]["era_id"]
        print(f"Block received: {block_hash}, Era: {era_id}")
        era_end = block["block"]["header"]["era_end"]
        if era_end is not None:
            next_era = era_id + 1
            print(f"Adding validator data for Era {next_era}")
            self._add_era_data(next_era, era_end["next_era_validator_weights"])


def stream_block_finalization():
    """
    Main method to announce block reception and finalization.
    """
    era_data = EraData()

    # Store finalized_block used to announce so we only announce once
    finalized_block_hash = ''
    # Loop through all messages streamed out and process
    for msg in event_stream_messages():
        if not msg:
            continue
        json_data = json.loads(msg.data)
        msg_type = next(iter(json_data.keys()))
        data = json_data[msg_type]
        if msg_type == "FinalitySignature":
            block_hash = data["block_hash"]
            if era_data.process_finality_signature(data) and finalized_block_hash != block_hash:
                finalized_block_hash = block_hash
                # This could be a call to your system marking a block finalized
                print(f"Block finalized: {finalized_block_hash}")
        elif msg_type == "BlockAdded":
            era_data.process_block(data)


stream_block_finalization()
