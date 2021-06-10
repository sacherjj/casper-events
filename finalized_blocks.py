from sseclient import SSEClient
import requests
from requests.exceptions import ConnectionError

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
# This example uses the SSE event stream from a node as this is event driven, provides the fastest responce, and
# eliminates polling of an RPC call.
#
# At startup, the validators weights is not known for the current Era, so this is retrieved via RPC calls.  This
# should be the only RPC calls needed and all further validator weights are taken from the switch block (last block) of
# the Era that comes in through the event stream.
#

BASE_SERVER = "3.14.161.135"
RPC_SERVER_URL = f"http://{BASE_SERVER}:7777/rpc"
SSE_SERVER_URL = f"http://{BASE_SERVER}:9999/events"


class EventStreamReader:
    """ Read the event stream of a casper-node """
    RECONNECT_DELAY_SEC = 5
    RECONNECT_COUNT = 1500

    def __init__(self, server_address: str, start_from: int = 0):
        self.server = server_address
        self.start_from = start_from
        self.last_msg_id = -1

    def messages(self):
        """
        Blocking method that continuously yields messages from the SSE server.
        """
        reconnect_count = 0
        while reconnect_count < self.RECONNECT_COUNT:
            reconnect_count += 1
            try:
                # On restart we might crawl through a bunch, but this doesn't miss them if it is a server restart.
                self.start_from = 0
                for message in SSEClient(f"{self.server}?start_from={self.start_from}"):
                    # SSE may send empty messages.  We ignore those.
                    if message.id is not None:
                        reconnect_count = 0
                        self.last_msg_id = int(message.id)
                        self.start_from = self.last_msg_id + 1
                        yield message
                print("Stream ended without error, retrying after delay.")
                sleep(self.RECONNECT_DELAY_SEC)
            except ConnectionError:
                print(f"Connection Error, last msg.id = {self.last_msg_id}, restarting after delay.")
                # Most likely server being restarted. Give some time before retry.
                sleep(self.RECONNECT_DELAY_SEC)
            except Exception as e:
                print(f"Error occurred: {e}")
        else:
            print(f"Reconnect count: {self.RECONNECT_COUNT} exceeded. Exiting...")


def rpc_call(method, params):
    url = RPC_SERVER_URL
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1})
    headers = {'content-type': "application/json", 'cache-control': "no-cache"}
    try:
        response = requests.request("POST", url, data=payload, headers=headers)
        json_data = json.loads(response.text)
        return json_data["result"]
    except Exception as e:
        print(f"Error during RPC call: {e}")


def get_block(block_hash=None, block_height=None):
    """
    Get block based on block_hash, block_height, or last block if block_identifier is missing
    """
    params = []
    if block_hash:
        params = [{"Hash": block_hash}]
    elif block_height:
        params = [{"Height": block_height}]
    return rpc_call("chain_get_block", params)


class EraData:
    def __init__(self):
        self._era_data = defaultdict(dict)
        # This is the main data structure that could be represented by a database or other store
        # {<era_id>:
        #           "weights": {<validator_key>: <validator_weight>, ...},
        #           "total_weight": <int total of all validator_weights>,
        #           "block_signatures": {"block_hash": [<public_key of validator signature>, ...], ...}
        # }

    def era_data(self, era_id: int) -> dict:
        """
        Returns data about that era.  If it does not exist, this is before we populated with
        era_end from the switch block stream, so we retrieve with the RPC with self._populate_validator_data().

        After the first switch block, this should not require RPC use.
        """
        if era_id not in self._era_data:
            self._populate_validator_data_from_rpc(era_id)
        return self._era_data[era_id]

    @staticmethod
    def _get_block_data_from_rpc(block_height=None) -> tuple:
        """
        Returns (height, era_id, era_end) from block queried by block_height.
        If no block_height is given it will return the latest block.
        """
        block_data = get_block(block_height=block_height)
        block_header = block_data["block"]["header"]
        return block_header["height"], block_header["era_id"], block_header["era_end"]

    def _prune_era_data(self, delete_era):
        """
        Remove data from self._era_data if era_id is before delete_before
        """
        for key in [key for key in self._era_data if key <= delete_era]:
            print(f"Removing Era data for era_id: {key}")
            del self._era_data[key]

    def _add_era_data(self, next_era_id, next_era_validator_weights):
        """
        Creates expected self._era_data structures and validator weights for block finalization detection
        """
        weights = {data["validator"]: int(data["weight"]) for data in next_era_validator_weights}
        self._era_data[next_era_id]["weights"] = weights
        self._era_data[next_era_id]["total_weight"] = sum(weights.values())
        self._era_data[next_era_id]["block_signatures"] = defaultdict(list)

        # We are pruning data to keep current and next as finalization signatures for the switch block
        # will come in after the switch block is received.
        self._prune_era_data(next_era_id - 2)

    def _populate_validator_data_from_rpc(self, era_id: int):
        """
        This loads initial validator weight information on startup as we have not received a switch block from the
        event stream yet.

        This should be used sparingly as it is VERY slow compared to just parsing the event stream.
        """
        block_height, cur_era_id, _ = self._get_block_data_from_rpc()

        switch_era_id_needed = era_id - 1  # switch block era_end shows the NEXT era validator weights

        # binary search for the switch block
        high_block_height = block_height
        low_block_height = 0
        era_end = None
        while era_end is None:
            try_block_height = (high_block_height - low_block_height) // 2 + low_block_height
            try_height, try_era_id, try_era_end = self._get_block_data_from_rpc(block_height=try_block_height)
            if try_era_id == switch_era_id_needed:
                if try_era_end:
                    era_end = try_era_end
                else:
                    low_block_height = try_block_height
            elif try_era_id < switch_era_id_needed:
                low_block_height = try_block_height
            else:
                high_block_height = try_block_height
        self._add_era_data(era_id, era_end["next_era_validator_weights"])

    def block_percent_signed_weight(self, block_hash: str, era_id: int) -> float:
        """
        returns the percentage of weight that has signed the block.

        This needs to be greater than 0.67 to be finalized.
        """
        ed = self.era_data(era_id)
        weight = 0
        for key in self._era_data[era_id]["block_signatures"][block_hash]:
            weight += ed["weights"].get(key, 0)
        return weight / ed["total_weight"]

    def process_finality_signature(self, fin_sig):
        """
        Processes the finality signature received from the event stream.

        Returns True is block has been finalized after including this signature
        """
        era_id = fin_sig["era_id"]
        block_hash = fin_sig["block_hash"]
        self.era_data(era_id)["block_signatures"][block_hash].append(fin_sig["public_key"])
        weight = self.block_percent_signed_weight(block_hash, era_id)
        return weight > 0.67

    def process_block(self, block):
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
    esr = EventStreamReader(SSE_SERVER_URL)
    era_data = EraData()

    # Store finalized_block used to announce so we only announce once
    finalized_block_hash = ''
    # Loop through all messages streamed out and process
    for msg in esr.messages():
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
