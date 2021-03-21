from sseclient import SSEClient, Event
from pathlib import Path
from time import sleep
from requests.exceptions import ConnectionError


class EventStreamReader:
    """ Read the event stream of a casper-node """
    RECONNECT_DELAY_SEC = 1
    RECONNECT_COUNT = 500

    def __init__(self, server_address: str, start_from=0):
        self.server = server_address
        self.start_from = start_from

    def _messages(self):
        messages = SSEClient(f"{self.server}?start_from={self.start_from}")
        for msg in messages:
            self.start_from = msg.id
            yield msg

    def messages(self):
        """
        Blocking method that continuously yields messages from the SSE server.

        Updates self.last_id for each message.  If SSE queue outruns client and is disconnected,
        it will resume at last_id.
        """
        reconnect_count = 0
        while reconnect_count < self.RECONNECT_COUNT:
            reconnect_count += 1
            try:
                for message in self._messages():
                    reconnect_count = 0
                    yield message
            except ConnectionError:
                sleep(self.RECONNECT_DELAY_SEC)


class EventStreamSimulator:

    def __init__(self, dump_file: Path, start_from=0):
        self.file_path = dump_file
        self.start_from = start_from

    def messages(self):
        """
        Simulates live event stream by using a dump file of the event stream from:
        `curl -sN host_ip:9999/events > dump_file`
        """
        # TODO: Implement start_from?
        for_processing = []
        for line in open(self.file_path, 'r'):
            if line == "\n":
                if for_processing != [':\n']:
                    yield Event.parse(''.join(for_processing))
                for_processing = []
                continue
            for_processing.append(line)
