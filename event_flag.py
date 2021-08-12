from event_stream_reader import EventStreamReader
from config import SSE_SERVER_MAIN_URL
from message_structure import MessageData

esr = EventStreamReader(SSE_SERVER_MAIN_URL)

for msg in esr.messages():
    if not msg:
        continue
    data = MessageData(msg.data)
    if data.is_block_added:
        proposer = data.data['block', 'body', 'proposer']
        # if proposer in ("01aa2976834459371b1cf7f476873dd091a0e364bd18abed8e77659b83fd892084",
        #                 "0163e03c3aa2b383f9d1b2f7c69498d339dcd1061059792ce51afda49135ff7876",
        #                 "01e61c8b8227afd8f7d4daece145546aa6775cf1c4ebfb6f3f56c18df558aed72d"):
        #     print(f"{data.data['block_hash']} Proposed block by Marco {proposer}")
        #     if proposer in "01e61c8b8227afd8f7d4daece145546aa6775cf1c4ebfb6f3f56c18df558aed72d":
        #         print("########################################")
        # else:
        #     print("not")
        if "010a78ee" in proposer:
            print(f"{data.data['block_hash']} Proposed block by Make {proposer}")
        else:
            print("not")
