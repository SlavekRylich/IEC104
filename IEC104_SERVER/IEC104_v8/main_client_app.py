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

    def get_evok_request(self, host: str, dev_type: str, circuit: str):
        url = f"http://{host}/rest/{dev_type}/{circuit}"
        return requests.get(url=url)
        # loop = asyncio.get_event_loop()
        # future1 = loop.run_in_executor(None, requests.get, url)
        # resp = await future1
        # return resp

    def send_evok_request(self, host: str, dev_type: str, circuit: str, value):
        url = f"http://{host}/rest/{dev_type}/{circuit}"
        data = {'value': str(int(value))}
        return requests.post(url=url, data=data)
        # loop = asyncio.get_event_loop()
        # future1 = loop.run_in_executor(None, requests.post, url, data)
        # resp = await future1
        # return resp

    def handle_evok_request_mapping(self, obj, config_IO: dict, value=None):
        dev_type = config_IO[obj]["pin"]
        circuit = config_IO[obj]["pin_id"]
        try:
            if dev_type == "di" or dev_type == "ai":
                ret = self.get_evok_request(host=self.evok_host, dev_type=dev_type, circuit=circuit)

            elif dev_type == "do" or dev_type == "ao":
                ret = self.send_evok_request(host=self.evok_host, dev_type=dev_type, circuit=circuit, value=value)
                # asyncio.sleep(1)    # musí se počkat než se data na patronu propíšou
                ret = self.send_evok_request(host=self.evok_host, dev_type=dev_type, circuit=circuit, value=value)
            else:
                logging.error(f"{dev_type} is not supported")
                ret = None

            return ret
        except Exception as e:
            logging.error(f"Error request for evok: {e}")
            return None

    def handle_gpio(self, obj, config_IO):
        pass

    async def handle_type_13(self, o_asdu, obj, config_IO, callback):
        pass

    async def handle_type_45(self, o_asdu, obj, config_IO, callback):
        method = config_IO[obj]["command_method"]

        value = obj.sco.on_off

        if method == "evok_api":
            ret = self.handle_evok_request_mapping(obj, config_IO, value)
        elif method == "gpio":
            self.handle_gpio(obj, config_IO)
        else:
            logging.error(f"{method} is not supported")

        # GENERATE RESPONSE
        value = ret.json()['result']['value']
        type_resp = 45
        sq = 0
        sq_count = 1
        test_bit = 0
        p_n_bit = 0
        org_OA = 0
        addr_COA = 1
        if o_asdu.cot == 6:
            # potvrzeni aktivace
            cot = 7  # 7 - ack activation
            sco = value  # 7 - activation
        elif o_asdu.cot == 8:
            # potvrzeni deaktivace
            cot = 9  # 7 - ack deactivation
            sco = value  # 7 - deactivation
        else:
            # unknown
            cot = 0
            sco = 0

        ioa = obj.ioa

        try:
            new_asdu = ASDU(type_id=type_resp,
                            sq=sq,
                            sq_count=sq_count,
                            test_bit=test_bit,
                            p_n_bit=p_n_bit,
                            cot=cot,
                            org_OA=org_OA,
                            addr_COA=addr_COA,
                            )

            new_obj = CScNa1(ioa=ioa, sco=sco)
            new_asdu.add_obj(new_obj)

            data = new_asdu.serialize()
            await self.on_send(data, callback)

        except Exception as e:
            logging.error(f"Exception in handle_type_45: {e}")

    async def handle_type_102(self, o_asdu, obj, config_IO, callback):
        method = config_IO[obj]["command_method"]

        if method == "evok_api":
            ret = self.handle_evok_request_mapping(obj, config_IO)
        elif method == "gpio":
            self.handle_gpio(obj, config_IO)
        else:
            logging.error(f"{method} is not supported")

        resistance = ret.json()["value"]
        temp = (20 * resistance) / 1077.9
        value = temp
        # GENERATE RESPONSE
        type_resp = 13
        sq = 0
        sq_count = 1
        test_bit = 0
        p_n_bit = 0
        cot = 5  # 5 - required
        org_OA = 0
        addr_COA = 1

        qds = 0
        ioa = obj.ioa

        try:
            new_asdu = ASDU(type_id=type_resp,
                            sq=sq,
                            sq_count=sq_count,
                            test_bit=test_bit,
                            p_n_bit=p_n_bit,
                            cot=cot,
                            org_OA=org_OA,
                            addr_COA=addr_COA,
                            )

            new_obj = MMeNc1(ioa=ioa, value=value, qds=qds)
            new_asdu.add_obj(new_obj)

            data = new_asdu.serialize()
            await self.on_send(data, callback)

        except Exception as e:
            logging.error(f"Exception in handle_type_102: {e}")


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
