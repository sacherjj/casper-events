import json


DEPLOY_PROCESSED = "DeployProcessed"
BLOCK_ADDED = "BlockAdded"
FINALITY_SIGNATURE = "FinalitySignature"


class NestedDict(dict):
    """
    Allows quick access of nested structure of a dict with tuple args

    {"key1": {"key2": {"key3": "here"}}}

    obj["key1", "key2", "key3"] == "here"
    obj["key1", "key3] == None
    """
    def __getitem__(self, key_tuple):
        # If simple key and not tuple, use dict interface
        if not isinstance(key_tuple, tuple):
            return super(NestedDict, self).get(key_tuple, None)
        d = self
        for key in key_tuple:
            d = d.get(key, None)
            if d is None:
                break
        return d


class MessageData:

    def __init__(self, json_str: str):
        json_data = json.loads(json_str)
        if len(json_data.keys()) > 1:
            raise ValueError("Expected message data to have only one root dict key")
        self.message_type = next(iter(json_data.keys()))
        self.data = NestedDict(json_data[self.message_type])

    def _fin_sig_pk(self):
        return f"finsig-{self.block_hash}-{self.data['public_key']}"

    def _block_pk(self):
        return f"block-{self.block_hash}"

    def _deploy_pk(self):
        return f"deploy-{self.data['deploy_hash']}"

    def is_type(self, type_name: str) -> bool:
        return self.message_type == type_name

    @property
    def is_deploy_processed(self):
        return self.is_type(DEPLOY_PROCESSED)

    @property
    def is_finality_signature(self):
        return self.is_type(FINALITY_SIGNATURE)

    @property
    def is_block_added(self):
        return self.is_type(BLOCK_ADDED)

    @property
    def primary_key(self):
        funcs = {FINALITY_SIGNATURE: self._fin_sig_pk,
                 BLOCK_ADDED: self._block_pk,
                 DEPLOY_PROCESSED: self._deploy_pk}
        return funcs[self.message_type]()

    @property
    def block_hash(self):
        return self.data["block_hash"]

    @property
    def era_id(self):
        # Does not exist for DeployProcessed so will be None

        # Finality Signature location
        era_id = self.data["era_id"]
        if era_id is None:
            # BlockAdded location
            return self.data["block", "header", "era_id"]
        return era_id