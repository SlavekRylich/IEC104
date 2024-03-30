# Import required modules
import gc
import sys
import time
import asyncio

from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat
from Parser import Parser
from config_loader import ConfigLoader
from Session import Session
from QueueManager import QueueManager

LISTENER_LIMIT = 5


class ServerIEC104:
    """
    Class for server IEC 104 protocol.
    """

    def __init__(self):
        """
        Constructor for server IEC 104 protocol.
        Args: None
        Returns: None
        Exceptions: None
        """
        self.config_loader = ConfigLoader('./v4.0/config_parameters.json')

        self.ip = self.config_loader.config['server']['ip_address']
        self.port = self.config_loader.config['server']['port']

        self.tasks = []
        self.clients: dict[str, QueueManager] = {}

        self.no_overflow = 0

        # central sleep time
        self.async_time = 0.5

        # load configuration parameters
        try:
            self.k, self.w, \
                self.timeout_t0, \
                self.timeout_t1, \
                self.timeout_t2, \
                self.timeout_t3 = self.load_params(self.config_loader)

            # save parameters into tuple 
            self.session_params = (self.k,
                                   self.w,
                                   self.timeout_t0,
                                   self.timeout_t1,
                                   self.timeout_t2,
                                   self.timeout_t3)

        except Exception as e:
            print(e)

    def load_params(self, config_loader):

        k = config_loader.config['server']['k']
        if k < 1 or k > 32767:
            raise Exception("Wrong value range for \'k\' variable!")

        w = config_loader.config['server']['w']
        if w > ((k * 2) / 3):
            if w < 1 or w > 32767:
                raise Exception("Wrong value range for \'w\' variable!")
            print(f"Warning! Use value range for "
                  "\'w\' less than 2/3 of \'k\'")

        t0 = config_loader.config['server']['t0']
        if t0 < 1 or t0 > 255:
            raise Exception("Wrong value range for \'t0\' variable!")

        t1 = config_loader.config['server']['t1']
        if t1 < 1 or t1 > 255:
            raise Exception("Wrong value range for \'t1\' variable!")

        t2 = config_loader.config['server']['t2']
        if t2 < 1 or t2 > 255:
            raise Exception("Wrong value range for \'t2\' variable!")

        t3 = config_loader.config['server']['t3']
        if t3 < 1 or t3 > 172800:
            raise Exception("Wrong value range for \'t3\' variable!")

        return k, w, t0, t1, t2, t3

    def send(self):
        pass

    async def listen(self):
        print(f"Naslouchám na {self.ip}:{self.port}")
        try:
            self._server = await asyncio.start_server(
                self.handle_client,
                self.ip,
                self.port,
            )


        except Exception as e:
            print(e)

    """
    Handle client.
    Args: reader, writer
    """

    async def handle_client(self, reader, writer):

        client_address, client_port = writer.get_extra_info('peername')

        """
        Create queue if not exist for that client.
        """
        if client_address not in self.clients:
            self.clients[client_address] = QueueManager(client_address, 'server')
            print(f"vytvorena nova fronta")
            queue = self.clients[client_address]

            if isinstance(queue, QueueManager):
                self.tasks.append(asyncio.create_task(queue.start()))

                # get own reference for check_alive_sessions in QueueManager class
                self.task_check_alive_queue = asyncio.create_task(
                    queue.check_alive_sessions(),
                )
                self.tasks.append(self.task_check_alive_queue)

        queue = self.clients[client_address]
        if isinstance(queue, QueueManager):

            session = Session(client_address,
                              client_port,
                              reader,
                              writer,
                              self.session_params,
                              queue,
                              'server')

            queue.add_session(session, )
            print(f"Spojení navázáno: s {client_address, client_port}, "
                  "(Celkem spojení: "
                  f"{queue.get_number_of_connected_sessions()}))")

            try:
                await session.start()

            except Exception as e:
                print(f"Exception {e}")
                pass

    async def run(self):

        self.task_periodic_event_check = asyncio.create_task(self.periodic_event_check())

        # while True:
        try:
            await asyncio.gather(self.task_periodic_event_check,
                                 *(task for task in self.tasks))

            await self._server.serve_forever()

        except Exception as e:
            print(f"Exception {e}")
            # continue

            # await asyncio.sleep(self.async_time)

    async def periodic_event_check(self):

        while True:
            print(f"Starting async server periodic event check.")
            try:
                # delete queue if no session is connected
                if len(self.clients) != 0:
                    if self.task_check_alive_queue.done():

                        for value in list(self.clients.values()):
                            if isinstance(value, QueueManager):
                                if value.flag_delete:
                                    result_value = self.clients.pop(value.ip)
                                    del result_value
                                    print(f"oddelano fronta ze slovniku")

                #     print(f"\r.")
                print(len(self.clients))
                gc.collect()
                objects = gc.get_objects()

                for value in list(self.clients.values()):
                    if isinstance(value, QueueManager):
                        print(f"value: {value}")
                found = False
                for obj in objects:
                    if isinstance(obj, QueueManager):
                        print(obj)
                        found = True

                if found:
                    print(f"Instatnce queue stale existuje")

                else:
                    print(f"Instatnce queue byla odstranena")

            except Exception as e:
                print(f"Exception {e}")

            print(f"Finish async server periodic event check.")
            await asyncio.sleep(self.async_time * 2)

    async def close(self):
        self._loop.close()

    # Main function


async def main():
    server = ServerIEC104()
    await server.listen()
    await server.run()


if __name__ == '__main__':

    server = ServerIEC104()
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass
    finally:
        pass
