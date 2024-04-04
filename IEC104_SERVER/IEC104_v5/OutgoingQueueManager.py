import asyncio
import logging

from Frame import Frame

# Nastavení úrovně logování
logging.basicConfig(
    filename='server_async.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Logování zprávy
logging.info("Toto je informační zpráva")
logging.warning("Toto je varovná zpráva")
logging.error("Toto je chybová zpráva")


class OutgoingQueueManager:

    def __init__(self, event: asyncio.Event = None):
        self._out_queue = asyncio.Queue(maxsize=256)

        if event is not None:
            self.__event_queue_out = event

    async def get_message(self, event: asyncio.Event = None):
        try:
            result = await self._out_queue.get()
            return result
        except asyncio.QueueEmpty:
            print(f"No data to send.")
            logging.error(f"No data to send.")

    def to_send(self, message_tuple: tuple[any, Frame], event: asyncio.Event):
        try:
            print(f"Přišlo do odchozí fronty: {message_tuple[1]}")
            logging.debug(f"Přišlo do odchozí fronty: {message_tuple[1]}")
            self._out_queue.put_nowait(message_tuple)
            if event:
                event.set()
            else:
                self.__event_queue_out.set()

        except asyncio.QueueFull:
            print(f"Out_Queue is full.")
            logging.error(f"Out_Queue is full.")

    def size(self):
        return self._out_queue.__sizeof__()

    def is_Empty(self):
        return self._out_queue.empty()

