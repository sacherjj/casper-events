import json
import requests

import config


def rpc_call(method, params):
    url = config.RPC_SERVER_URL
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1})
    headers = {'content-type': "application/json", 'cache-control': "no-cache"}
    try:
        response = requests.request("POST", url, data=payload, headers=headers)
        json_data = json.loads(response.text)
        return json_data["result"]
    except requests.exceptions.RequestException as e:
        print(e)
    except Exception as e:
        print(e)


def get_deploy(deploy_hash: str):
    """
    Get deploy by deploy_hash
    """
    return rpc_call("info_get_deploy", [deploy_hash])


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

