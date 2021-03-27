import json


DEPLOY_PROCESSED = "DeployProcessed"
BLOCK_ADDED = "BlockAdded"
FINALITY_SIGNATURE = "FinalitySignature"


class MessageData(dict):
    """
    Allows quick access of nested structure of a dict with tuple args

    {"key1": {"key2": {"key3": "here"}}}

    obj["key1", "key2", "key3"] == "here"
    obj["key1", "key3] == self.NOT_FOUND_VALUE
    """
    NOT_FOUND_VALUE = None

    @staticmethod
    def from_json(json_str: str):
        json_data = json.loads(json_str)
        return NestedDict(json_data)

    def __getitem__(self, key_tuple):
        # If simple key and not tuple, use dict interface
        if not isinstance(key_tuple, tuple):
            return super(MessageData, self).get(key_tuple, self.NOT_FOUND_VALUE)
        d = self
        for key in key_tuple:
            d = d.get(key, self.NOT_FOUND_VALUE)
            if d == self.NOT_FOUND_VALUE:
                break
        return d

    @property
    def message_type(self):
        if len(self.keys()) > 1:
            raise ValueError("Expected message data to have only one root dict key")
        return next(iter(self.keys()))

    def _fin_sig_pk(self):
        return f"finsig-{self['block_hash']}-{self['public_key']}"

    def _block_pk(self):
        return f"block-{self['block_hash']}"

    def _deploy_pk(self):
        return f"deploy-{self['deploy-hash']}"

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
        return funcs[self.get_message_type()]()

    @property
    def era_id(self):
        # Does not exist for DeployProcessed so will be NOT_FOUND_VALUE

        # Finality Signature location
        era_id = self["era_id"]
        if era_id is self.NOT_FOUND_VALUE:
            # BlockAdded location
            return self["block", "header", "era_id"]
