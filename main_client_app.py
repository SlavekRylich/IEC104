# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import sys
import time

import requests

import ASDU
from Mapper_IO import IEC101Mapper
from client_app import IEC104Client
from server import ServerIEC104
from ASDU import *


class Main:
    def __init__(self):
        self.cb_on_send = None
        self.session = None
        self.tasks = []

        self.client = IEC104Client()
        self.client.register_callback_on_connect = self.on_connect
        self.client.register_callback_on_message = self.on_message
        self.client.register_callback_on_disconnect = self.on_disconnect

        # self.mapper = IEC101Mapper()
        # self.evok_host = self.mapper.host
        # self.mapping_IEC101 = {
        #     13: self.handle_type_13,
        #     45: self.handle_type_45,
        #     102: self.handle_type_102
        # }

    # async def input(self):
    #     start_time = time.time()
    #     debounce_time = 0.2
    #     while not self.client.stop:

    async def main(self):
        try:
            task = asyncio.create_task(self.client.start())
            self.tasks.append(task)
            # self.tasks.append(asyncio.create_task(self.read_input()))

            task = asyncio.create_task(self.client.connect("192.168.1.10", 2404))
            self.tasks.append(task)

            # while not self.client.stop:
            #     key = input("zadej: \n")
            #     if key == 'q':
            #         self.client.stop = True
            #         break

            # TODO
            # while True:
            for task in self.tasks:
                await asyncio.gather(*self.tasks)
                # await task
            await asyncio.sleep(1)
        except Exception as e:
            logging.error(f"Error with run task server in main(): {e}")
        finally:
            self.client.close()

    def on_connect(self, host, port, rc):
        if rc == 0:
            print(f"Established with new client: {host}:{port}")
            logging.info(f"Established with new client: {host}:{port}")
        else:
            logging.error(f"Connection refused with client!")
        pass

    async def on_message(self, session, apdu, data, cb_on_sent):

        o_asdu = ASDU(data)

        print(f"Receive type id: {o_asdu.type_id}")
        if o_asdu.type_id == 13:
            for obj in o_asdu.objs:
                if isinstance(obj, MMeNc1):
                    temp = float("{:.3f}".format(obj.value))
                    print(f"Temperature: {temp}°C")

        # for obj in o_asdu.objs:
        #
        #     config_IO[obj] = self.mapper.handle_iec101_message(obj.ioa)
        #     if config_IO[obj] is not None:
        #         # callback
        #         for type_id in self.mapping_IEC101.keys():
        #             if type_id == obj.type_id:
        #                 callback = (session, cb_on_sent)
        #                 await self.mapping_IEC101[type_id](o_asdu, obj, config_IO, callback)

    async def on_send(self, response, callback):
        try:
            await callback[1](callback[0], response)

        except Exception as e:
            logging.error(f"Exception in on_send: {e}")

    def on_disconnect(self, session):
        logging.debug(f"deleted {session} from clientmanager")
        logging.info(f"{session.name} {session.ip}:{session.port} disconnected!")
        pass


if __name__ == "__main__":
    code = Main()
    try:
        if sys.platform.lower() == "win32" or os.name.lower() == "nt":
            from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

            set_event_loop_policy(WindowsSelectorEventLoopPolicy())
        # Run your async application as usual
        asyncio.run(code.main())

    except KeyboardInterrupt:
        pass
    finally:
        pass
