import asyncio
import logging

import requests

import ASDU
from Mapper_IO import IEC101Mapper
from server import ServerIEC104
from ASDU import *


class Main:
    def __init__(self):
        self.cb_on_send = None
        self.session = None
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
            if config_IO[obj] is not None:
                # callback
                for type_id in self.mapping_IEC101.keys():
                    if type_id == obj.type_id:
                        callback = (session, cb_on_sent)
                        await self.mapping_IEC101[type_id](o_asdu, obj, config_IO, callback)

    async def on_send(self, response, callback):
        try:
            await callback[1](callback[0], response)

        except Exception as e:
            print(f"Exception: {e}")
            logging.error(f"Exception: {e}")

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

    def handle_evok_request_mapping(self, obj, config_IO: dict, value=None):
        dev_type = config_IO[obj]["pin"]
        circuit = config_IO[obj]["pin_id"]

        if dev_type == "di" or dev_type == "ai":
            # ret = self.get_evok_request(host=self.evok_host, dev_type=dev_type, circuit=circuit)
            # print(ret.json())
            ret = None

        elif dev_type == "do" or dev_type == "ao":
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
            print(f"{method} is not supported")
            logging.error(f"{method} is not supported")

        # GENERATE RESPONSE
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
            sco = 1  # 7 - activation
        elif o_asdu.cot == 8:
            # potvrzeni deaktivace
            cot = 9  # 7 - ack deactivation
            sco = 0  # 7 - deactivation
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
            print(e)
            logging.error(e)

    async def handle_type_102(self, o_asdu, obj, config_IO, callback):
        method = config_IO[obj]["command_method"]

        if method == "evok_api":
            ret = self.handle_evok_request_mapping(obj, config_IO)
        elif method == "gpio":
            self.handle_gpio(obj, config_IO)
        else:
            print(f"{method} is not supported")
            logging.error(f"{method} is not supported")

        print(f"none {ret}")
        # value = ret["value"]

        # GENERATE RESPONSE
        type_resp = 13
        sq = 0
        sq_count = 1
        test_bit = 0
        p_n_bit = 0
        cot = 5  # 5 - required
        org_OA = 0
        addr_COA = 1

        value = 20.2
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
            print(e)
            logging.error(e)


if __name__ == "__main__":
    code = Main()
    try:
        asyncio.run(code.main())

    except KeyboardInterrupt:
        pass
    finally:
        pass
