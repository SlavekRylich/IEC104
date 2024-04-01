# -*- coding: utf-8 -*-
# import readline
import os
import sys
import struct
import logging
import time
import asyncio

from Parser import Parser
from QueueManager import QueueManager
from config_loader import ConfigLoader
import Session
from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat

LOG = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)


class IEC104Client(object):
    def __init__(self):
        self.queue = None
        self.active_session = None
        self.servers = {}
        self.data = 'vymyslena data'
        self.data1 = 0x65 + \
                     0x01 + \
                     0x0A + \
                     0x00 + \
                     0x0C + \
                     0x00 + \
                     0x00 + \
                     0x00 + \
                     0x00 + \
                     0x05

        self.__event = asyncio.Event()

        self.loop = None
        self.no_overflow = 0
        self.async_time = 0.8

        self.data2 = struct.pack(f"{'B' * 10}",
                                 0x65,  # start byte
                                 0x01,  # Total Length pouze hlavička
                                 0x0A,  # 1. ridici pole
                                 0x00,  # 2. ridici pole
                                 0x0C,  # 3. ridici pole
                                 0x00,  # 4. ridici pole hlavička
                                 0x00,  # 1. ridici pole
                                 0x00,  # 2. ridici pole
                                 0x00,  # 3. ridici pole
                                 0x05,  # 3. ridici pole
                                 )

        self.data_list = [self.data2, self.data2]  # define static data

        config_loader = ConfigLoader('./v4.0/config_parameters.json')

        self.server_ip = config_loader.config['server']['ip_address']
        self.server_port = config_loader.config['server']['port']

        # load configuration parameters
        try:
            self.k, self.w, \
                self.timeout_t0, \
                self.timeout_t1, \
                self.timeout_t2, \
                self.timeout_t3 = self.load_params(config_loader)

            self.session_params = (self.k,
                                   self.w,
                                   self.timeout_t0,
                                   self.timeout_t1,
                                   self.timeout_t2,
                                   self.timeout_t3)

        except Exception as e:
            print(e)

    def set_loop(self, loop):
        self.loop = loop

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

    async def new_session(self, ip, port):
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.timeout_t0
            )

            client_address, client_port = self.writer.get_extra_info('sockname')
            print(f"Navázáno {client_address}:{client_port}"
                  f"-->{self.server_ip}:{self.server_port}")

            callback_handle_apdu = self.queue.handle_apdu
            callback_timeouts = (self.queue.handle_timeout_t0,
                                 self.queue.handle_timeout_t1,
                                 self.queue.handle_timeout_t2,
                                 self.queue.handle_timeout_t3)

            new_session = Session.Session(self.server_ip,
                                          self.server_port,
                                          self.reader,
                                          self.writer,
                                          self.session_params,
                                          callback_handle_apdu,
                                          callback_timeouts,
                                          'client')

            self.queue.add_session(new_session)
            self.active_session = self.queue.Select_active_session()
            return self.active_session

        except asyncio.TimeoutError:
            print(f"{time.ctime()} - Nastala chyba: {self.active_session}")
            pass
        except Exception as e:
            print(e)

    async def run_client(self, ip, port_num):

        loop = asyncio.get_event_loop_policy().get_event_loop()
        self.set_loop(loop)

        self.queue = QueueManager(ip)
        self._in_queue = self.queue.in_queue
        self._out_queue = self.queue.out_queue
        self._send_buffer = self.queue.send_buffer
        self._recv_buffer = self.queue.recv_buffer
        self.task_queue = asyncio.create_task(self.queue.start())

        try:
            print(f"Vytáčím {self.server_ip}:{self.server_port}")

            # přidá novou session a zároveň vybere aktivní session
            self.active_session = await self.new_session(ip, port_num)

            if isinstance(self.active_session, Session.Session):
                self.servers[ip] = self.queue

                # set start session flag
                self.active_session.flag_session = 'START_SESSION'

                self.task_periodic_event_check = asyncio.create_task(
                    self.periodic_event_check()
                )

                self.task_handle_response = asyncio.create_task(
                    self.queue.handle_response_for_client(self.active_session)
                )

                self.task_check_alive_queue = asyncio.create_task(
                    self.queue.check_alive_sessions(),
                )
                await asyncio.gather(self.task_periodic_event_check,
                                     self.task_queue,
                                     self.task_check_alive_queue)

                # await asyncio.sleep(self.async_time)

        except Exception as e:
            print(f"Exception: {e}")

    async def periodic_event_check(self):
        print(f"Starting async periodic event check.")
        while True:
            print(f"Starting async server periodic event check.")
            try:
                # delete queue if no session is connected
                if len(self.servers) != 0:
                    if self.task_check_alive_queue.done():

                        for value in list(self.servers.values()):
                            if isinstance(value, QueueManager):
                                if value.flag_delete:
                                    del self.servers[value.ip]

                # UI se nebude volat tak často jako ostatní metody
                self.no_overflow = self.no_overflow + 1
                if self.no_overflow > 2:
                    self.no_overflow = 0

                    await self.task_handle_response
                    print(f"no_overflow bezi")

                await asyncio.sleep(self.async_time)

            except TimeoutError as e:
                print(f"TimeoutError {e}")
                pass

            except Exception as e:
                print(f"Exception {e}")


if __name__ == "__main__":

    # host = "192.168.1.142"
    host = "127.0.0.1"
    port = 2404

    client = IEC104Client()
    try:
        asyncio.run(client.run_client(host, port))
    except KeyboardInterrupt:
        pass
    finally:
        pass
