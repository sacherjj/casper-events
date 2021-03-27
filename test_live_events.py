from event_stream_reader import EventStreamReader
import time


server_path = "http://18.220.220.20:9999/events"

esr = EventStreamReader(server_path, 80000)
esr.RECONNECT_DELAY_SEC = 0.1
esr.RECONNECT_COUNT = 15

last_id = 0
for msg in esr.messages():
    print(msg.id, msg)
    if last_id + 1 != int(msg.id):
        print(f"ID skip: {last_id} -> {msg.id}")
    last_id = int(msg.id)