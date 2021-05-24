from event_stream_reader import EventStreamReader, file_message_streamer_with_disconnects


# With changes to always pull from 0 and overwrite old data
# This many never finish.  With server restarts, the id resets
# to 0, so we cannot safely resume if the error was due to upgrade.

data_path = "events_dryrun_120"

esr = EventStreamReader(data_path, 70122, file_message_streamer_with_disconnects)
esr.RECONNECT_DELAY_SEC = 0.5
esr.RECONNECT_COUNT = 15

for msg in esr.messages():
    print(msg.id, msg)
