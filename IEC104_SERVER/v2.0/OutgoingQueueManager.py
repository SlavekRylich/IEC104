from QueueManager import QueueManager

class OutgoingQueueManager(QueueManager):
    async def on_message_sent(self, message_id):
        # Zpracuje potvrzení o doručení
        # ...
        # Odstranit zprávu z dočasného úložiště
        pass