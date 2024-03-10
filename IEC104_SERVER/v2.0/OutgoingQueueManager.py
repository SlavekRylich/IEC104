import asyncio
from QueueManager import QueueManager

class OutgoingQueueManager(QueueManager):
    
    def __init__(self):
        self._out_queue = asyncio.Queue()
    
    async def on_message_sent(self, message_id):
        # Zpracuje potvrzení o doručení
        # ...
        # Odstranit zprávu z dočasného úložiště
        pass
    
    async def get_message(self):
        return await self._out_queue.get()
    
    async def receive(self, message):
            self._out_queue.put_nowait(message)
            
    def size(self):
        return self._out_queue.__sizeof__
    
    
    def is_Empty(self):
        return self._out_queue.empty