from event_stream_reader import EventStreamReader
from config import SSE_SERVER_URL
from message_structure import MessageData
from collections import defaultdict

esr = EventStreamReader(SSE_SERVER_URL)

era_proposers = {}
for msg in esr.messages():
    if not msg:
        continue
    data = MessageData(msg.data)
    if data.is_block_added:
        era_id = data.data['block', 'header', 'era_id']
        if era_id not in era_proposers:
            era_proposers[era_id] = defaultdict(int)
        proposer = data.data['block', 'body', 'proposer']
        era_proposers[era_id][proposer] += 1
        if data.data['block', 'header', 'height'] == 47264:
            break

print(era_proposers)
