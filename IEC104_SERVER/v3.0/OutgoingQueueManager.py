import asyncio

class OutgoingQueueManager():
    
    def __init__(self):
        self._out_queue = asyncio.Queue(maxsize=256)
    
    async def on_message_sent(self, message_id):
        # Zpracuje potvrzení o doručení
        
        # Odstranit zprávu z dočasného úložiště
        pass
    
    def get_message(self):
        try:
            res = self._out_queue.get_nowait()
            self._out_queue.task_done()
            return res
        except asyncio.QueueEmpty:
            print(f"No data to send.")
    
    async def to_send(self, message):
        try:
            print(f"Přišlo do odchozí fronty: {message}")
            self._out_queue.put_nowait(message)
            
        except asyncio.QueueFull:
            print(f"Out_Queue is full.")
            
    def size(self):
        return self._out_queue.__sizeof__()
    
    
    def is_Empty(self):
        return self._out_queue.empty()