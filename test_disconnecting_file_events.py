from event_stream_reader import EventStreamReader, file_message_streamer_with_disconnects


data_path = "events_dryrun"

esr = EventStreamReader(data_path, 70122, file_message_streamer_with_disconnects)
esr.RECONNECT_DELAY_SEC = 0.5
esr.RECONNECT_COUNT = 15

for msg in esr.messages():
    print(msg.id, msg)