import config
from jsonrpcclient import request


def get_block(block_hash: str) -> str:
    result = request(config.RPC_SERVER_URL,
                     "chain_get_block",
                     {"Hash": block_hash})
    return result.data.result


def generate_finality_signatures_for_block(block_hash):
    """ returns array of FinalitySignature event messages for a block """
    result = get_block(block_hash)
    block = result["block"]
    era_id = int(block["header"]["era_id"])
    hash = block["hash"]
    # When hash is bad, chain_get_block returns last block
    assert block_hash == hash
    proofs = block["proofs"]
    finality_signatures = []
    for proof in proofs:
        public_key = proof["public_key"]
        signature = proof["signature"]
        finality_signatures.append({"FinalitySignature":
                                       {"block_hash": block_hash,
                                        "era_id": era_id,
                                        "signature": signature,
                                        "public_key": public_key}
                                   })
    return finality_signatures
