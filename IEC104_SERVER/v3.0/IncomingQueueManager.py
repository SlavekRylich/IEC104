import asyncio
import time


from Frame import Frame

class IncomingQueueManager():
    
    
    # def __init__(self, *args, **kwargs):
    def __init__(self):
    
        self._in_queue = asyncio.Queue(maxsize=256)
    
    
    async def on_message(self, message: Frame):
        # Zpracuje zprávu z příchozí fronty
        
        # Odeslat potvrzení klientovi
        pass
    
    async def on_message_received(self, message: Frame):
            print(f"Přišlo do příchozí fronty: {message}")
            await self._in_queue.put(message)
            
    async def get_message(self):
        return await self._in_queue.get()
    
    async def is_overflow(self):
        # return True if queue is greater than 90% of max size
        if len(self._in_queue) >= self._in_queue.maxsize*0.9:
            return True
        return False
    
    def size(self):
        return self._in_queue.__sizeof__()
    
    
    def is_Empty(self):
        return self._in_queue.empty()
    
    