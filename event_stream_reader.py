from sseclient import SSEClient, Event
from time import sleep
from requests.exceptions import ConnectionError
import random
import logging


def node_message_streamer(server: str, start_from: int = 0):
    """ yields messages from a node server """
    messages = SSEClient(f"{server}?start_from={start_from}")
    for msg in messages:
        yield msg


def file_message_streamer(server: str, start_from):
    """
    Simulates live event stream by using a dump file of the event stream from:
    `curl -sN host_ip:9999/events > dump_file`

    server should be full path to file
    """
    for_processing = []
    for line in open(server, 'r'):
        if line == "\n":
            if for_processing != [':\n']:
                msg = Event.parse(''.join(for_processing))
                cur_id = int(msg.id) if msg.id is not None else 0
                if cur_id >= int(start_from):
                    yield msg
            for_processing = []
            continue
        for_processing.append(line)


def file_message_streamer_with_disconnects(server: str, start_from: int):
    """ Call file_message_streamer with random ConnectionErrors """
    error_step = random.randint(0, 1000)
    cur_step = 0
    for msg in file_message_streamer(server, start_from):
        cur_step += 1
        if cur_step >= error_step:
            raise ConnectionError("Fake connection error from file_message_streamer_with_disconnects")
        yield msg


class EventStreamReader:
    """ Read the event stream of a casper-node """
    RECONNECT_DELAY_SEC = 5
    RECONNECT_COUNT = 1500

    def __init__(self, server_address: str, start_from: int = 0, message_streamer=None):
        self.server = server_address
        self.start_from = start_from
        self.last_msg_id = -1
        if message_streamer is None:
            self._message_streamer = node_message_streamer
        else:
            self._message_streamer = message_streamer

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
                # On restart we might crawl through a bunch, but this doesn't miss them if it is a server restart.
                self.start_from = 0
                for message in self._message_streamer(self.server, self.start_from):
                    # SSE may send empty messages.  We ignore those.
                    if message.id is not None:
                        reconnect_count = 0
                        self.last_msg_id = int(message.id)
                        self.start_from = self.last_msg_id + 1
                        yield message
                logging.info("Stream ended without error, retrying after delay.")
                sleep(self.RECONNECT_DELAY_SEC)
            except ConnectionError:
                logging.error(f"Connection Error, last msg.id = {self.last_msg_id}, restarting after delay.")
                # Most likely server being restarted. Give some time before retry.
                sleep(self.RECONNECT_DELAY_SEC)
            except Exception as e:
                logging.error(f"Error occurred: {e}")
                sleep(self.RECONNECT_DELAY_SEC)
        else:
            logging.error(f"Reconnect count: {self.RECONNECT_COUNT} exceeded. Exiting...")

