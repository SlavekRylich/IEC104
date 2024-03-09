class Server:
    def __init__(self):
        self._clients = {}

    def listen(self, host, port):
        self._server = asyncio.start_server(self.on_new_connection, host, port)

    async def on_new_connection(self, reader, writer):
        ip_address = reader.get_extra_info('peername')[0]
        if ip_address not in self._clients:
            self._clients[ip_address] = QueueManager()
        session = Session(reader, writer, self._clients[ip_address])
        session.start()

    async def run(self):
        await self._server
        await asyncio.gather(*[session.run() for session in self._clients.values()])

class QueueManager:
    def __init__(self):
        self._sessions = []
        self._queue = Queue()

    def add_message(self, message):
        self._queue.put_nowait(message)

    async def get_message(self):
        return await self._queue.get()

    async def on_message_sent(self, message_id):
        # Zpracuje potvrzení o doručení zprávy
        pass

    async def run(self):
        while True:
            message = await self._queue.get()
            for session in self._sessions:
                await session.send_message(message)

class Session:
    def __init__(self, reader, writer, queue_manager):
        self._reader = reader
        self._writer = writer
        self._queue_manager = queue_manager

    def start(self):
        asyncio.create_task(self.on_data_received())
        asyncio.create_task(self.run())

    async def on_data_received(self):
        while True:
            data = await self._reader.read(1024)
            frame = Frame.parse(data)
            # Zpracuje přijatý frame

    async def send_message(self, message):
        data = message.serialize()
        self._writer.write(data)

    async def run(self):
        while True:
            await asyncio.sleep(1)
            # Zkontroluje, zda klient neodeslal data



class Server:
    def __init__(self):
        self._incoming_queue = IncomingQueueManager()
        self._outgoing_queue = OutgoingQueueManager()

    def listen(self, host, port):
        self._server = asyncio.start_server(self.on_new_connection, host, port)

    async def on_new_connection(self, reader, writer):
        session = Session(reader, writer, self._incoming_queue, self._outgoing_queue)
        session.start()

    async def run(self):
        await self._server
        await asyncio.gather(*[session.run() for session in self._clients.values()])

class QueueManager:
    def __init__(self):
        self._queue = Queue()

    def add_message(self, message):
        self._queue.put_nowait(message)

    async def get_message(self):
        return await self._queue.get()

    async def run(self):
        while True:
            message = await self._queue.get()
            # Zpracuje zprávu
            pass

class IncomingQueueManager(QueueManager):
    async def on_message_received(self, message):
        # Zpracuje zprávu z příchozí fronty
        # ...
        # Odeslat potvrzení klientovi

class OutgoingQueueManager(QueueManager):
    async def on_message_sent(self, message_id):
        # Zpracuje potvrzení o doručení
        # ...
        # Odstranit zprávu z dočasného úložiště

class Session:
    def __init__(self, reader, writer, incoming_queue, outgoing_queue):
        self._reader = reader
        self._writer = writer
        self._incoming_queue = incoming_queue
        self._outgoing_queue = outgoing_queue

    def start(self):
        asyncio.create_task(self.on_data_received())
        asyncio.create_task(self.run())

    async def on_data_received(self):
        while True:
            data = await self._reader.read(1024)
            frame = Frame.parse
