import json
import datetime


API_VERSION = "ApiVersion"
DEPLOY_PROCESSED = "DeployProcessed"
DEPLOY_ACCEPTED = "DeployAccepted"
BLOCK_ADDED = "BlockAdded"
FINALITY_SIGNATURE = "FinalitySignature"
STEP = "Step"
FAULT = "Fault"


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
        self.full_msg = json_str
        json_data = json.loads(json_str)
        if len(json_data.keys()) > 1:
            raise ValueError("Expected message data to have only one root dict key")
        self.message_type = next(iter(json_data.keys()))
        # ApiVersion is a scalar so using whole data
        if self.message_type == API_VERSION:
            self.data = NestedDict(json_data)
        else:
            self.data = NestedDict(json_data[self.message_type])

    def _fin_sig_pk(self):
        return f"finsig-{self.block_hash}-{self.data['public_key']}"

    def _block_pk(self):
        return f"block-{self.block_hash}"

    def _deploy_pk(self):
        return f"deploy-{self.data['deploy_hash']}"

    def _deploy_accepted_pk(self):
        return f"deploy-accepted-{self.data['hash']}"

    def _api_pk(self):
        return f"api-{self.data[API_VERSION].replace('.', '_')}"

    def _step_pk(self):
        return f"step-{self.data['era_id']}"

    @staticmethod
    def _unique_timestamp():
        return f"{datetime.datetime.now().timestamp()}"

    def _fault_pk(self):
        return f"fault-{self._unique_timestamp()}"

    def _unknown_pk(self):
        return f"unknown-{self._unique_timestamp()}"

    def is_type(self, type_name: str) -> bool:
        return self.message_type == type_name

    @property
    def is_api_version(self):
        return self.is_type(API_VERSION)

    @property
    def is_deploy(self):
        return self.is_deploy_accepted or self.is_deploy_processed

    @property
    def is_deploy_processed(self):
        return self.is_type(DEPLOY_PROCESSED)

    @property
    def is_deploy_accepted(self):
        return self.is_type(DEPLOY_ACCEPTED)

    @property
    def is_finality_signature(self):
        return self.is_type(FINALITY_SIGNATURE)

    @property
    def is_block_added(self):
        return self.is_type(BLOCK_ADDED)

    @property
    def is_step(self):
        return self.is_type(STEP)

    @property
    def primary_key(self):
        funcs = {FINALITY_SIGNATURE: self._fin_sig_pk,
                 BLOCK_ADDED: self._block_pk,
                 DEPLOY_PROCESSED: self._deploy_pk,
                 DEPLOY_ACCEPTED: self._deploy_accepted_pk,
                 STEP: self._step_pk,
                 FAULT: self._fault_pk}
        func = funcs.get(self.message_type, self._unknown_pk)
        return func()

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
