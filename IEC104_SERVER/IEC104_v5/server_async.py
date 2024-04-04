# Import required modules
import gc
import logging
import asyncio


from config_loader import ConfigLoader
from Session import Session
from QueueManager import QueueManager

# Nastavení úrovně logování
logging.basicConfig(
    filename='server_async.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Logování zprávy
logging.info("Toto je informační zpráva")
logging.warning("Toto je varovná zpráva")
logging.error("Toto je chybová zpráva")


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
        self.__loop = None
        self.task_check_alive_queue = None
        self._server = None
        self.config_loader = ConfigLoader('../IEC104_v5/config_parameters.json')

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
        logging.info(f"Naslouchám na {self.ip}:{self.port}")
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

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        This function is called when a new client connects to the server. It creates a new QueueManager object for
        the client if one does not already exist, and adds it to the "self.clients" dictionary. Args: reader (
        asyncio.StreamReader): A stream reader for the incoming data from the client. writer (asyncio.StreamWriter):
        A stream writer for sending data to the client.
        """
        client_addr, client_port = writer.get_extra_info('peername')
        """
        Get the IP address of the client that connected to the server.
        """
        if client_addr not in self.clients:
            self.clients[client_addr] = QueueManager(client_addr, 'server')
            print(f"Created new queue for client {client_addr}")
            logging.info(f"Created new queue for client {client_addr}")
            queue = self.clients[client_addr]

            if isinstance(queue, QueueManager):
                pass
                # Start the queue processing task
                # self.tasks.append(asyncio.create_task(queue.start()))

                # Get a reference to the task that checks for inactive sessions
                # self.task_check_alive_queue = asyncio.create_task(
                #     queue.check_alive_sessions()
                # )
                # self.tasks.append(self.task_check_alive_queue)

        queue = self.clients[client_addr]

        # Get the functions to call for handling incoming APDU packets and timeout events
        callback_handle_apdu = queue.on_handle_message
        callback_timeouts_tuple = (
            queue.handle_timeout_t0,
            queue.handle_timeout_t1,
            queue.handle_timeout_t2,
            queue.handle_timeout_t3,
        )

        if isinstance(queue, QueueManager):
            # Create a new Session object for the client
            session = Session(
                client_addr,
                client_port,
                reader,
                writer,
                self.session_params,
                callback_handle_apdu,
                callback_timeouts_tuple,
                queue.send_buffer,
                'server'
            )

            # Add the session to the queue
            queue.add_session(session)
            print(f"Connection established with {client_addr}:{client_port} "
                  f"(Total connections: {queue.get_number_of_connected_sessions()})")
            logging.info(f"Connection established with {client_addr}:{client_port} "
                         f"(Number of connections: {queue.get_number_of_connected_sessions()})")

            try:
                # Start the session
                await session.start()

            except Exception as e:
                print(f"Exception: {e}")
                logging.error(f"Exception: {e}")

    async def run(self):
        self.__loop = asyncio.get_running_loop()
        pass
        # self.task_periodic_event_check = asyncio.create_task(self.periodic_event_check())

        # # while True:
        # try:
        #     await asyncio.gather(self.task_periodic_event_check,
        #                          *(task for task in self.tasks))
        #
        await self._server.serve_forever()
        #
        # except Exception as e:
        #     print(f"Exception {e}")
        # continue

        # await asyncio.sleep(self.async_time)

    async def periodic_event_check(self):

        while True:
            print(f"Starting async server periodic event check.")
            logging.debug(f"Starting async server periodic event check.")
            try:
                # delete queue if no session is connected
                if len(self.clients) != 0:
                    if self.task_check_alive_queue.done():

                        for value in list(self.clients.values()):
                            if isinstance(value, QueueManager):
                                if value.flag_delete:
                                    result_value = self.clients.pop(value.ip)
                                    print(f"oddelana fronta ze slovniku {result_value}")
                                    logging.debug(f"oddelana fronta ze slovniku {result_value}")
                                    del result_value

                print(len(self.clients))
                gc.collect()
                objects = gc.get_objects()

                for value in list(self.clients.values()):
                    if isinstance(value, QueueManager):
                        print(f"value: {value}")
                        logging.debug(f"value: {value}")

                found = False
                for obj in objects:
                    if isinstance(obj, QueueManager):
                        print(obj)
                        found = True

                if found:
                    print(f"Instatnce queue stale existuje")
                    logging.debug(f"Instatnce queue stale existuje")

                else:
                    print(f"Instatnce queue byla odstranena")
                    logging.debug(f"Instatnce queue byla odstranena")

            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

            print(f"Finish async server periodic event check.")
            logging.debug(f"Finish async server periodic event check.")
            await asyncio.sleep(self.async_time * 2)

    async def close(self):
        self.__loop.close()
        logging.info(f"Loop.close!")
        logging.shutdown()


# Main function
async def main():
    my_server = ServerIEC104()
    await my_server.listen()
    await my_server.run()


if __name__ == '__main__':

    server = ServerIEC104()
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass
    finally:
        pass
