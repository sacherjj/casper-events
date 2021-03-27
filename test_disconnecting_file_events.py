from event_stream_reader import EventStreamReader, file_message_streamer_with_disconnects


data_path = "delta-11_event_stream_16280"

esr = EventStreamReader(data_path, 20122, file_message_streamer_with_disconnects)
esr.RECONNECT_DELAY_SEC = 0.1
esr.RECONNECT_COUNT = 15

for msg in esr.messages():
    print(msg.id, msg)
