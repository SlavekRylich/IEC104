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
    
    
    async def on_message_received(self, message):
        # Zpracuje zprávu z příchozí fronty
        # ...
        # Odeslat potvrzení klientovi
        pass
    
    async def receive(self, message):
            self._in_queue.put_nowait(message)
            
    def size(self):
        return self._in_queue.__sizeof__
    
    
    def is_Empty(self):
        return self._in_queue.empty
    
    
    async def handle_messages(self, session: Session):
        try:
            new_apdu = await session.handle_messages()
            if new_apdu:
                self.receive(new_apdu)
            
             
        except asyncio.TimeoutError:
            print(f'Klient {self} neposlal žádná data.')
            
        except Exception as e:
            print(f"Exception {e}")