import socket
import pickle
import acpi
import time

class CommModule:
    def __init__(self, socket):
        self.socket = socket
        self.connected = False
    
    def send_data(self, data):
        serialized_data = pickle.dumps(data)
        self.socket.sendall(serialized_data)

    def receive_data(self):
        serialized_data = self.socket.recv(1024)
        return pickle.loads(serialized_data)
    
    def send_start_act(self):
        self.send_data(acpi.STARTDT_ACT)
        print("Odeslán start act.")
        
    def send_start_con(self):
        self.send_data(acpi.STARTDT_CON)
        print("Odeslán start con.")
        
    def receive_start_act(self):
        data = self.receive_data()
        if data == acpi.STARTDT_ACT:
            print("Pokus o navázání spojení.")
        else:
            print("Chyba komunikace.")
            
    def receive_start_con(self):
        data = self.receive_data()
        print(data)
        if data == acpi.STARTDT_CON:
            self.connected = True
            print("Spojení úspěšně navázáno.")
        else:
            print("Chyba spojení.")
    
            
    def connection_timeout(self, socket):
        time.sleep(30)
        if not self.connected:
            print("Chyba: Časový limit pro připojení vypršel.")
            self.socket.close()
    
