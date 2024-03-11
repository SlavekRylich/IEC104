import asyncio
import time


from Frame import Frame
from QueueManager import QueueManager
from Parser import Parser
from Session import Session

class IncomingQueueManager():
    
    
    # def __init__(self, *args, **kwargs):
    def __init__(self):
    
        self._in_queue = asyncio.Queue(maxsize=256)
    
    
    async def on_message_received(self, message: Frame):
        # Zpracuje zprávu z příchozí fronty
        # ...
        # Odeslat potvrzení klientovi
        self.receive(message)
        pass
    
    async def receive(self, message):
            self._in_queue.put_nowait(message)
            
    def size(self):
        return self._in_queue.__sizeof__
    
    
    def is_Empty(self):
        return self._in_queue.empty
    
    