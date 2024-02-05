# -*- coding: utf-8 -*-
import socket
import binascii
import acpi
import asdu
import json
import struct
import logging
from config_loader import ConfigLoader
from communication_modul import CommModule
import threading

LOG = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)


class IEC104Client(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.comm_module = CommModule(self.client_socket)
        self.ssn = 0    # send sequence number
        self.rsn = 0    # receive sequence number
        self.connected = False

    def send_data(self, data):
        self.comm_module.send_data(data)

    def receive_data(self):
        return self.comm_module.receive_data()

if __name__ == "__main__":
    
    config_loader = ConfigLoader('config_parameters.json')
    client = IEC104Client(config_loader.config['client']['ip_address'], config_loader.config['client']['port'])

    threading.Thread(target=client.comm_module.connection_timeout, args=(client,)).start()
    client.comm_module.send_start_act()
    client.comm_module.receive_start_con()
    
    
    # Example: Send data to the server
    # client_data = {"message": "Hello from the client!"}
    # start_byte = b'\x68'    
    # client_data_bytes = json.dumps(client_data).encode('utf-8')
    # length_byte = struct.pack("H", len(client_data_bytes))
    # print(len(client_data_bytes))
    # client.send_data(start_byte + length_byte + client_data_bytes)

    # # Example: Receive data from the server
    # server_response = client.receive_data()
    # print(f"Received response from server: {server_response}")