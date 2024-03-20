import asyncio

from Frame import Frame

class OutgoingQueueManager():
    
    def __init__(self, event: asyncio.Event = None):
        self._out_queue = asyncio.Queue(maxsize=256)
        
        if event is not None:
            self.__event_out = event
    
    async def get_message(self, event: asyncio.Event = None):
        try:
            result = await self._out_queue.get()
            return result
        except asyncio.QueueEmpty:
            print(f"No data to send.")
    
    async def to_send(self, message_tuple: tuple[any, Frame]):
        try:
            print(f"Přišlo do odchozí fronty: {message_tuple[1]}")
            self._out_queue.put_nowait(message_tuple)
            self.__event_out.set()
            
        except asyncio.QueueFull:
            print(f"Out_Queue is full.")
            
    def size(self):
        return self._out_queue.__sizeof__()
    
    
    def is_Empty(self):
        return self._out_queue.empty()