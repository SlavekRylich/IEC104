import asyncio
import time


from Frame import Frame

class IncomingQueueManager():
    
    
    # def __init__(self, *args, **kwargs):
    def __init__(self, event: asyncio.Event = None):
    
        self._in_queue = asyncio.Queue(maxsize=256)
        
        if event is not None:
            self.__event_queue_in = event
    
    def on_message_received(self, message_tuple: tuple[any, Frame]):
        try:
            print(f"Přišlo do příchozí fronty: {message_tuple[1]}")
            self._in_queue.put_nowait(message_tuple)
            self.__event_queue_in.set()
            
        except asyncio.QueueFull:
            print(f"In_Queue is full.")
            
    async def get_message(self):
        try:
            result = await self._in_queue.get()
            return result
        
        except asyncio.QueueEmpty:
            print(f"No data on receive.")
    
    async def is_overflow(self):
        # return True if queue is greater than 90% of max size
        if len(self._in_queue) >= self._in_queue.maxsize*0.9:
            return True
        return False
    
    def size(self):
        return self._in_queue.__sizeof__()
    
    
    def is_Empty(self):
        return self._in_queue.empty()
    
    