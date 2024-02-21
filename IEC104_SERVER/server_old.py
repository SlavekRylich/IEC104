import acpi
import asdu
import socket
import struct
import logging
import binascii
from config_loader import ConfigLoader
from CommModule import CommModule
from multiprocessing import Process
from bitstring import BitStream
import Frame

LOG = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)


class IEC104Server(object):

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.active_session = False
        self.connected = False
        self.type_frame = ""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))

    def start(self):
        self.server_socket.listen(2)
        print(f"Server listening on {self.ip}:{self.port}")
        
        while True:
            self.client_socket, client_address = self.server_socket.accept()            
            self.client_handler = Process(target=self.handle_client, args=(self.client_socket, client_address,))
            self.client_handler.start()

    def handle_client(self, client_socket, client_address):
        
        comm_module = CommModule(client_socket)
        frame = Frame.Frame()
        try:
            self.client_socket.settimeout(acpi.T0)
            print(f"[NEW CONNECTION] {client_address} connected.")
            self.connected = True
            packet = comm_module.receive_data()
            
            header = packet[0]
            if (header[2] & 3) == 3: 
                print(f"U format {header[2] & 0xFF}")
                self.type_frame = "U"
                header = header[2]
                print(header)
                if self.type_frame == "U":
                    if header == acpi.STARTDT_ACT:
                        data = frame.pack(acpi.STARTDT_CON)
                        comm_module.send_data(data)
                        print("prijato startdt act, posilam startdt con")
                        self.active_session = True
                    elif header == acpi.STOPDT_ACT:
                        data = frame.pack(acpi.STOPDT_CON)
                        comm_module.send_data(data)
                        print("prijato stopdt act, posilam stopdt con")
                        self.active_session = False
                    elif header == acpi.TESTFR_ACT:
                        data = frame.pack(acpi.TESTFR_CON)
                        comm_module.send_data(data)
                        print("prijato testdt act, odeslano testdt. spojeni je aktivní")
                    else:
                        print("prislo neco divneho")
                        
                else:
                    self.type_frame = ""
            
            
            
        
            try:
                packet = comm_module.receive_data()
            except:
                pass                      
            header = packet[0]
            data = packet[1]
            if not (header[2] & 1):
                print(f"I format {header[2] & 0xFF}")
                self.type_frame = "I"
            elif (header[2] & 3) == 1:
                print(f"S format {header[2] & 0xFF}")
                self.type_frame = "S"
            elif (header[2] & 3) == 3: 
                print(f"U format {header[2] & 0xFF}")
                self.type_frame = "U"
                header = header[2]
                print(header)
            else:
                print("Nejaky jiny format")
            
            if self.type_frame == "I":
                pass
            elif self.type_frame == "S":
                pass
            elif self.type_frame == "U":
                if header == acpi.STARTDT_ACT:
                    data = frame.pack(acpi.STARTDT_CON)
                    comm_module.send_data(data)
                    print("prijato startdt act, posilam startdt con")
                    self.active_session = True
                elif header == acpi.STOPDT_ACT:
                    data = frame.pack(acpi.STOPDT_CON)
                    comm_module.send_data(data)
                    print("prijato stopdt act, posilam stopdt con")
                    self.active_session = False
                elif header == acpi.TESTFR_ACT:
                    data = frame.pack(acpi.TESTFR_CON)
                    comm_module.send_data(data)
                    print("prijato testdt act, odeslano testdt. spojeni je aktivní")
                else:
                    print("prislo neco divneho")
                    
            else:
                self.type_frame = ""
                
                print("ukoncen prenos, spojeni stale aktivní")
        except socket.timeout:
            print(f"Timeout - žádná data od klienta {client_address} během 30 sekund.")
            # Zde můžete provést akce při timeoutu, například uzavření spojení a restart serveru
            print("Konec spojení")
            client_socket.close()
        

        except socket.error as e:
            print(f"Chyba při komunikaci s klientem {client_address}: {e}")

        # finally:
        #     # Uzavření soketu
            
        #     print("Konec spojení")
        #     client_socket.close()
            
            

if __name__ == "__main__":
    config_loader = ConfigLoader('config_parameters.json')
    server = IEC104Server(config_loader.config['server']['ip_address'], config_loader.config['server']['port'])
    server.start()
        