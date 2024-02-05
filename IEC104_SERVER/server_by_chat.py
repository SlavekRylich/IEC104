# Import required modules
import socket
import threading
import acpi
import asdu
import struct
import logging
from config_loader import ConfigLoader
from CommModul import CommModule
import Frame

HOST = '127.0.0.1'
PORT = 1234 # You can use any port between 0 to 65535
LISTENER_LIMIT = 5

class ServerIEC104():
    
    # constructor for IEC104 server
    def __init__(self, ip, port): 
        self.ip = ip
        self.port = port
        self.active_session = False
        self.connected = False
        self.type_frame = ""
        
        self.active_clients = [] # List of all currently connected users
    
    # Function to listen for upcoming messages from a client
    def listen_for_messages(self,client, username):

        while 1:

            message = client.recv(2048).decode('utf-8')
            if message != '':
                
                final_msg = username + '~' + message
                self.send_messages_to_all(final_msg)

            else:
                print(f"The message send from client {username} is empty")

    # Function for identify what format it is
    def what_format(self, header):
        if not (header[2] & 1):
            print(f"I format {header[2] & 0xFF}")
            return "I"
        elif (header[2] & 3) == 1:
            print(f"S format {header[2] & 0xFF}")
            return "S"
        elif (header[2] & 3) == 3: 
            print(f"U format {header[2] & 0xFF}")
            return "U"
        else:
            print("Nejaky zpičený format")
            return None
        
    # Function to send message to a single client
    def send_message_to_client(self,client, message):

        client.sendall(message.encode())

    # Function to send any new message to all the clients that
    # are currently connected to this server
    def send_messages_to_all(self,message):
        
        for user in self.active_clients:

            self.send_message_to_client(user[1], message)
    
    def active_transmission(self,client_socket, client_addr):
        # kód pro indetifikaci přenosu uživatelských dat
        try:
            #client_socket.settimeout(acpi.T0)
            
            # Server will listen for client message that will contain the username
            while True:
                
                header = self.comm_module.receive_length()
                
                #if username != '':
                if header != '':
                    #prompt_message = "SERVER~" + f"{username} added to the chat"
                    #self.send_messages_to_all(prompt_message)
                    
                    self.type_frame = self.what_format(header)
                    
                    if self.type_frame == "I":
                        # here is code that receive a rest of data
                        pass
                    
                    elif self.type_frame == "S":
                        # here is code that confirms correct reception of I format message
                        pass
                    
                    elif self.type_frame == "U":                        
                        if header == acpi.STARTDT_ACT:
                            self.comm_module.send_data(self.frame.pack(acpi.STARTDT_CON))
                            print("prijato startdt act, posilam startdt con")
                            self.active_session = True
                            
                        elif header == acpi.STOPDT_ACT:
                            self.comm_module.send_data(self.frame.pack(acpi.STOPDT_CON))
                            print("prijato stopdt act, posilam stopdt con a přenos je ukončen")
                            self.active_session = False
                            break
                        
                        elif header == acpi.TESTFR_ACT:
                            self.comm_module.send_data(self.frame.pack(acpi.TESTFR_CON))
                            print("prijato testdt act, odeslano testdt. spojeni je aktivní")
                            
                        else:
                            print("prislo neco divneho")
                else:
                    #print("Client username is empty")
                    print("Receive packet is empty")
            
            ## procedura pro udržování aktivního spojení pomocí testdt mezi klientem a serverem
            
        except socket.timeout:
            print(f"Timeout - žádná data od klienta {client_addr} během {acpi.T0} sekund.")
            
        except Exception as e:
            print(f"Chyba při komunikaci s klientem {client_addr}: {e}")
            
        finally:
            pass

    # Function to handle client
    def client_handler(self,client_socket, client_addr):
        
        try:
            client_socket.settimeout(acpi.T0)
            # Server will listen for client message that will contain the username
            while True:
                
                #username = client.recv(2048).decode('utf-8')
                # receive header for unpack header bytes
                header = self.comm_module.receive_length()
                
                
                #if username != '':
                if header != '':
                    #prompt_message = "SERVER~" + f"{username} added to the chat"
                    #self.send_messages_to_all(prompt_message)
                    
                    if (header[2] & 3) == 3: # U format
                        header = header[2]
                        print(header)       # byte
                        
                        if header == acpi.STARTDT_ACT:
                            self.comm_module.send_data(self.frame.pack(acpi.STARTDT_CON))
                            print("prijato startdt act, posilam startdt con")
                            self.active_session = True
                            threading.Thread(target=self.active_transmission, args=(client_socket, client_addr, )).start()
                        else:
                            print("prislo neco divneho")
                else:
                    #print("Client username is empty")
                    print("Receive packet is empty")
            
            ## procedura pro udržování aktivního spojení pomocí testdt mezi klientem a serverem
            
        except socket.timeout:
            print(f"Timeout - žádná data od klienta {client_addr} během {acpi.T0} sekund.")
            
        except Exception as e:
            print(f"Chyba při komunikaci s klientem {client_addr}: {e}")
            
        finally:
            self.active_clients.remove((client_socket, client_addr))
            client_socket.close()

    # Main function
    def start(self):

        # Creating the socket class object
        # AF_INET: we are going to use IPv4 addresses
        # SOCK_STREAM: we are using TCP packets for communication
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.comm_module = CommModule(server_socket)
        self.frame = Frame.Frame()

        # Creating a try catch block
        try:
            # Provide the server with an address in the form of
            # host IP and port
            server_socket.bind((self.ip, self.port))
            print(f"Running the server on {self.ip} {self.port}")
            
            # Set server limit
            server_socket.listen(LISTENER_LIMIT)
            
        except:
            print(f"Unable to bind to host {self.ip} and port {self.port}")


        # This while loop will keep listening to client connections
        while True:

            client, address = server_socket.accept()
            print(f"Successfully connected to client {address[0]} {address[1]}")
            self.active_clients.append((client, address))
            
            threading.Thread(target=self.client_handler, args=(client, address, )).start()


if __name__ == '__main__':
    config_loader = ConfigLoader('config_parameters.json')
    server = ServerIEC104(config_loader.config['server']['ip_address'], config_loader.config['server']['port'])
    server.start()