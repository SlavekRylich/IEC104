from QueueManager import QueueManager

class IncomingQueueManager(QueueManager):
    async def on_message_received(self, message):
        # Zpracuje zprávu z příchozí fronty
        # ...
        # Odeslat potvrzení klientovi
        pass