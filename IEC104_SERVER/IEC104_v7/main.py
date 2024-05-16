import asyncio
import logging

from server import ServerIEC104
from ASDU import ASDU


def on_connect(host, port, rc):
    print(host)
    print(port)
    print(rc)
    if rc == 0:
        print(f"Established with new client: {host}:{port}")
        logging.info(f"Established with new client: {host}:{port}")
    else:
        print(f"Connection refused!")
        logging.error(f"Connection refused!")
    pass


async def on_message(session, apdu, data, cb_on_sent):

    print(f"Here is data: {data}")
    o_data = ASDU(data)
    print(o_data)
    response = "Resp"
    await cb_on_sent(session, response.encode('ascii'))


def on_send():
    pass


def on_disconnect(session):
    print(f"{session.name}, {session.ip}:{session.port} disconnect!")
    logging.debug(f"deleted {session} from clientmanager")
    logging.info(f"{session.name} {session.ip}:{session.port} disconnected!")
    pass


async def main():
    tasks = []
    server = ServerIEC104()
    server.register_callback_on_connect = on_connect
    server.register_callback_on_message = on_message
    server.register_callback_on_send = on_send
    server.register_callback_on_disconnect = on_disconnect

    task = asyncio.create_task(server.start())
    tasks.append(task)

    # TODO
    # while True:
    for task in tasks:
        await asyncio.gather(*tasks)
        # await task
    await asyncio.sleep(1)
    server.close()


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass
    finally:
        pass
