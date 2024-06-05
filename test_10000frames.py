import asyncio

from Config_loader import ConfigLoader
from Frame import Frame
from Parser import Parser
from UFormat import UFormat
from apci import APCI


async def main(host, port, count_frames, pause):
    loop = asyncio.get_running_loop()
    stop = False
    count = 0
    count_i = 0

    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(host, port),
        timeout=10
    )

    frame = UFormat(APCI.TESTFR_ACT)

    for i in range(0, count_frames):
        # self.__out_queue.to_send((session, frame), session_event)
        writer.write(frame.serialize())
        await writer.drain()
        await asyncio.sleep(pause)
        count_i += 1
    print(count_i)

    while not stop:
        header = await asyncio.wait_for(reader.read(2), timeout=10)
        if header:
            start_byte, frame_length = header
            # identify IEC 104
            if start_byte == Frame.start_byte():
                # read the rest of frame
                apdu = await reader.read(frame_length)
                if len(apdu) == frame_length:
                    new_apdu = Parser.parser(apdu, frame_length)
                    if new_apdu.type_of_Uformat_Str == 'TESTDT CON':
                        count += 1
                    if count == count_frames:
                        stop = True

    print(f"Receive count: {count}")


if __name__ == "__main__":

    config_loader: ConfigLoader = ConfigLoader('./config_parameters.json')
    server_ip = config_loader.config['server']['ip_address']
    server_port = config_loader.config['server']['port']

    config_test: ConfigLoader = ConfigLoader('./config_10000frames.json')
    count_test_frames = config_test.config['test']['count']
    test_pause = config_test.config['test']['pause'] / 1000  # to ms
    try:
        asyncio.run(main(server_ip, server_port, count_test_frames, test_pause))
    except KeyboardInterrupt:
        pass
    finally:
        pass
