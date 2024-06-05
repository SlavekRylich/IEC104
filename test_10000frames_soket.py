# -*- coding: utf-8 -*-
import asyncio
import socket
import time

from Config_loader import ConfigLoader
from Frame import Frame
from Parser import Parser
from UFormat import UFormat
from apci import APCI





def send_and_receive_frame(host, port, count_test_frames, test_pause):
  """Otevře TCP socket, odešle rámec a čeká na odpověď."""
  frame = UFormat(APCI.TESTFR_ACT).serialize()
  count_i = 0
  count = 0

  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Připojení k serveru
    s.connect((host, port))

    for i in range(0, count_test_frames):
        # self.__out_queue.to_send((session, frame), session_event)

        s.send(frame)
        time.sleep(test_pause)

        count_i += 1
    print(count_i)

    # Čekání na odpověď
    while True:
        header = s.recv(2)
        if header:
            start_byte, frame_length = header
            # identify IEC 104
            if start_byte == Frame.start_byte():
                # read the rest of frame
                apdu = s.recv(frame_length)
                if len(apdu) == frame_length:
                    new_apdu = Parser.parser(apdu, frame_length)
                    if new_apdu.type_of_Uformat_Str == 'TESTDT CON':
                        count += 1
        break

    # Vypisování odpovědi
    print("Odpověď:", new_apdu)


async def main(server_ip, server_port, count_test_frames, test_pause):
    loop = asyncio.get_running_loop()
    stop = False
    count = 0
    count_i = 0

    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(server_ip, server_port),
        timeout=10
    )

    frame = UFormat(APCI.TESTFR_ACT)

    for i in range(0, count_test_frames):
        # self.__out_queue.to_send((session, frame), session_event)
        writer.write(frame.serialize())
        await writer.drain()
        await asyncio.sleep(test_pause)
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
                    if count == count_test_frames:
                        stop = True

    print(f"Receive count: {count}")


if __name__ == "__main__":

    config_loader: ConfigLoader = ConfigLoader('./config_parameters.json')
    server_ip = config_loader.config['server']['ip_address']
    server_port = config_loader.config['server']['port']

    config_test: ConfigLoader = ConfigLoader('./config_10000frames.json')
    count_test_frames = config_test.config['test']['count']
    test_pause = config_test.config['test']['pause'] / 1000  # to ms

    send_and_receive_frame(server_ip, server_port, count_test_frames,test_pause)

    # try:
    #     asyncio.run(main(server_ip, server_port, count_test_frames, test_pause))
    # except KeyboardInterrupt:
    #     pass
    # finally:
    #     pass
