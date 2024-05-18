import asyncio
import logging

import requests

import ASDU
from mapper3 import IEC101Mapper
from server import ServerIEC104
from ASDU import *


class Main:
    def __init__(self):
        self.tasks = []
        self.server = ServerIEC104()
        self.server.register_callback_on_connect = self.on_connect
        self.server.register_callback_on_message = self.on_message
        self.server.register_callback_on_send = self.on_send
        self.server.register_callback_on_disconnect = self.on_disconnect
        self.mapper = IEC101Mapper()
        self.evok_host = self.mapper.host
        self.mapping_IEC101 = {
            13: self.handle_type_13,
            45: self.handle_type_45,
            102: self.handle_type_102
        }

    async def main(self):
        task = asyncio.create_task(self.server.start())
        self.tasks.append(task)

        # TODO
        # while True:
        for task in self.tasks:
            await asyncio.gather(*self.tasks)
            # await task
        await asyncio.sleep(1)
        self.server.close()

    def on_connect(self, host, port, rc):
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

    async def on_message(self, session, apdu, data, cb_on_sent):

        o_asdu = ASDU(data)
        config_IO = {}

        for obj in o_asdu.objs:

            config_IO[obj] = self.mapper.handle_iec101_message(obj.ioa)
            if not None:
                # callback
                for type_id in self.mapping_IEC101.keys():
                    if type_id == obj.type_id:
                        response = self.mapping_IEC101[type_id](obj, config_IO)

        print(o_asdu)
        response_add = obj.ioa
        response = o_asdu.serialize()
        if not response:
            await self.on_send(session, response, cb_on_sent)

    async def on_send(self, session, response, cb_on_sent):
        await cb_on_sent(session, response.encode('ascii'))
        pass

    def on_disconnect(self, session):
        print(f"{session.name}, {session.ip}:{session.port} disconnect!")
        logging.debug(f"deleted {session} from clientmanager")
        logging.info(f"{session.name} {session.ip}:{session.port} disconnected!")
        pass

    def get_evok_request(self, host: str, dev_type: str, circuit: str):
        url = f"http://{host}/rest/{dev_type}/{circuit}"
        return requests.get(url=url)

    def send_evok_request(self, host: str, dev_type: str, circuit: str, value):
        url = f"http://{host}/rest/{dev_type}/{circuit}"
        data = {'value': str(int(value))}
        return requests.post(url=url, data=data)

    def handle_evok_request_mapping(self, obj, config_IO: dict):
        dev_type = config_IO[obj]["pin"]
        circuit = config_IO[obj]["pin_id"]

        if dev_type == "di" or dev_type == "ai":
            # ret = self.get_evok_request(host=self.evok_host, dev_type=dev_type, circuit=circuit)
            # print(ret.json())
            ret = None

        elif dev_type == "do" or dev_type == "ao":
            value = obj.value
            # ret = self.send_evok_request(host=self.evok_host, dev_type=dev_type, circuit=circuit, value=value)
            # print(ret.json())
            ret = None
        else:
            print(f"{dev_type} is not supported")
            logging.error(f"{dev_type} is not supported")
            ret = None

        return ret

    def handle_gpio(self, obj, config_IO):
        pass

    def handle_type_13(self, obj, config_IO):
        method = config_IO[obj]["command_method"]

        if method == "evok_api":
            ret = self.handle_evok_request_mapping(obj, config_IO)
        elif method == "gpio":
            self.handle_gpio(obj, config_IO)
        else:
            print(f"{method} is not supported")
            logging.error(f"{method} is not supported")

        # get value from ret
        print(ret)

        # create response type 13
        # response = self.generate_type_13(obj, value)
        # await self.on_send(session, response, cb_on_sent)
        pass
        print(config_IO)
        return None

    def handle_type_45(self, obj, config_IO):
        method = config_IO[obj]["command_method"]
        dev_type = config_IO[obj]["pin"]

        if method == "evok_api":
            ret = self.handle_evok_request_mapping(obj, config_IO)
        elif method == "gpio":
            self.handle_gpio(obj, config_IO)
        else:
            print(f"{method} is not supported")
            logging.error(f"{method} is not supported")

        print(ret)
        if obj.sco.on_off == 1:
            # potvrzeni aktivace
            resp = b'\x2D\x01\x07\x00\x0C\x00\x10\x30\x00\x00'
        else:
            # potvrzeni deaktivace
            resp = b'\x2D\x01\x09\x00\x0C\x00\x10\x30\x00\x00'
        response = ASDU.ASDU(resp)
        return resp

    def handle_type_102(self, obj, config_IO):
        method = config_IO[obj]["command_method"]
        dev_type = config_IO[obj]["pin"]

        if method == "evok_api":
            ret = self.handle_evok_request_mapping(obj, config_IO)
        elif method == "gpio":
            self.handle_gpio(obj, config_IO)
        else:
            print(f"{method} is not supported")
            logging.error(f"{method} is not supported")

        print(ret)


if __name__ == "__main__":
    code = Main()
    try:
        asyncio.run(code.main())

    except KeyboardInterrupt:
        pass
    finally:
        pass
