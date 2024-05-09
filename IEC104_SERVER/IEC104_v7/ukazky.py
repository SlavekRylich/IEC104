import asyncio


class ServerIEC104:
    def __init__(self, name: str = "Server"):
        self.ip = "127.0.0.1"
        self.port = 2404


async def handle_client(reader, writer):
    pass


async def main():
    my_server = ServerIEC104()
    server = await asyncio.start_server(handle_client, my_server.ip, my_server.port)
    await server.serve_forever()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        pass


async def handle_messages(self) -> None:
    while not self.__flag_stop_tasks:
        try:
            header = await asyncio.wait_for(self.__reader.read(2), timeout=self.__timeout_t1)

            if header:
                start_byte, frame_length = header

                if start_byte == Frame.start_byte():
                    apdu = await self.__reader.read(frame_length)

                    if len(apdu) == frame_length:
                        new_apdu = Parser.parser(apdu, frame_length)
                        self.__timer_t0.start()
                        self.__timer_t1.start()
                        self.__timer_t2.start()
                        self.__timer_t3.start()
                        asyncio.ensure_future(self.__callback_on_message_recv(self, new_apdu))

                        header = None
                        start_byte = None
                        apdu = None
                        new_apdu = None
                        frame_length = None

            if self.__reader.at_eof():
                self.flag_session = 'ACTIVE_TERMINATION'
                asyncio.ensure_future(self.__callback_on_message_recv(self))
                break

        except asyncio.TimeoutError:
            if self.__connection_state != 'DISCONNECTED':
                pass


async def handle_client(self, reader: asyncio.StreamReader,
                        writer: asyncio.StreamWriter) -> None:
    # získá IP adresu a port z TCP spojení
    client_addr, client_port = writer.get_extra_info('peername')
    # callback pro smazání instance ClientManagera pokud již nemá žádné aktivní spojení
    callback = self.check_alive_clients
    # vytvoøení instance ClientManager, pokud se pøipojil nový klient
    if client_addr not in self.clients:
        client_manager_instance = ClientManager(client_addr,
                                                port=None,
                                                callback_check_clients=callback,
                                                callback_only_for_client=None,
                                                server_name=self.name,
                                                whoami='server')
        # pøiøazení vytvoøené instance do slovníku s IP adresou jako její index
        self.clients[client_addr] = client_manager_instance
    # získání reference na instanci pokud již exitovala døíve
    client_manager_instance: ClientManager = self.clients[client_addr]
    # callback funkce pro pøedání v argumentu
    callback_on_message_recv = client_manager_instance.on_message_recv_or_timeout
    callback_timeouts_tuple: tuple = (
        client_manager_instance.handle_timeout_t0,
        client_manager_instance.handle_timeout_t1,
        client_manager_instance.handle_timeout_t2,
        client_manager_instance.handle_timeout_t3,
    )
    # vytvoøení nové instance Session uvnitø instance ClientManager
    session = client_manager_instance.add_session(client_addr,
                                                  client_port,
                                                  reader,
                                                  writer,
                                                  self.session_params,
                                                  callback_on_message_recv,
                                                  callback_timeouts_tuple,
                                                  whoami='server')

    try:
        # spuštìní asynchroní smyèky pro pøíjem dat ve tøídì session
        await session.start()

    except Exception as e:
        print(f"Exception: {e}")
        logging.error(f"Exception: {e}")

    async def on_message_recv_or_timeout(self, session: Session, apdu: Frame = None) -> None:
        # pokud metodu spustil pøijatý ramec, zpracuj ho, pokud ne tak to byl timeout
        if apdu is not None:

            # vložení rámce do vyrovnávací pamìti k potvrzení
            if isinstance(apdu, IFormat):
                self.__recv_buffer.add_frame(apdu.ssn, apdu)
            # jedná-li se o øízenou stanici, jinak øídicí stanice
            if self.__whoami == 'server':
                # zpracování dat
                await self.handle_apdu(session, apdu)
                # aktualizace stavu spojení
                await self.update_state_machine_server(session, apdu)
            else:
                await self.handle_apdu(session, apdu)
                await self.update_state_machine_client(session, apdu)

        else:
            if self.__whoami == 'server':
                await self.update_state_machine_server(session)
            else:
                await self.update_state_machine_client(session)


async def handle_timeout_t0(self, session: Session = None) -> None:
    logging.debug(f"Timer t0 timed_out - {session}")
    logging.debug(f'Client {session.ip}:{session.port} timed out and disconnected')
    session.flag_session = 'ACTIVE_TERMINATION'


async def handle_timeout_t1(self, session: Session = None) -> None:
    logging.debug(f"Timer t1 timed_out - {session}")
    session.flag_timeout_t1 = 1
    asyncio.ensure_future(self.on_message_recv_or_timeout(session))


async def handle_timeout_t2(self, session: Session = None) -> None:
    logging.debug(f"Timer t2 timed_out - {session}")
    if not self.__recv_buffer.is_empty():
        new_frame = await self.generate_s_frame(session)
        task = asyncio.ensure_future(session.send_frame(new_frame))
        self.__tasks.append(task)


async def handle_timeout_t3(self, session: Session = None) -> None:
    logging.debug(f"Timer t3 timed_out - {session}")
    new_frame = self.generate_testdt_act()
    task = asyncio.ensure_future(session.send_frame(new_frame))
    self.__tasks.append(task)


async def send_frame(self, frame: Frame = None) -> None:
    if not self.__flag_stop_tasks:

        try:
            if frame is not None:
                logging.info(f"{time.strftime('%X')}-Send"
                             f" to {self.ip}:{self.port}"
                             f" - frame: {frame}")
                self.__writer.write(frame.serialize())
                await self.__writer.drain()
            # add to packet buffer
            if isinstance(frame, IFormat):
                self.__send_buffer.add_frame(frame.ssn, frame)

        except Exception as e:
            logging.error(f"Exception {e}")
