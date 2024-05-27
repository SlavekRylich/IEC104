import asyncio

from server import ServerIEC104



async def main(server):
    my_server = ServerIEC104()
    my_server.register_callback_on_connect = on_connect
    my_server.register_callback_on_message = on_message
    my_server.register_callback_on_disconnect = on_disconnect

    task_server = asyncio.create_task(my_server.start())

    # your code ...

    await task_server

if __name__ == "__main__":
    asyncio.run(main())
