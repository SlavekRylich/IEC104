import socket
import threading
import time

class Frame:
    def __init__(self, frame_type, payload):
        self.frame_type = frame_type
        self.payload = payload

    def to_bytes(self):
        # Implementace serializace rámce na bajty
        pass

    @classmethod
    def from_bytes(cls, data):
        # Implementace deserializace bajtů na instanci třídy Frame
        pass

class IFrame(Frame):
    def __init__(self, sequence_number, payload):
        super().__init__("I", payload)
        self.sequence_number = sequence_number

class SFrame(Frame):
    def __init__(self, ack_number):
        super().__init__("S", None)
        self.ack_number = ack_number

class UFrame(Frame):
    def __init__(self, control_type):
        super().__init__("U", None)
        self.control_type = control_type

class CommModule:
    def __init__(self, socket):
        self.socket = socket
        self.lock = threading.Lock()

    def send_frame(self, frame):
        # Odeslat rámec přes soket
        pass

    def receive_frame(self):
        # Přijmout rámec ze soketu
        pass

    def start(self):
        # Spustit vlákno pro nepřetržitě čtení ze soketu
        pass

class Server:
    def __init__(self, address):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(address)
        self.server_socket.listen()
        self.clients = []

    def accept_clients(self):
        # Přijímat klienty a vytvářet pro ně vlákna
        pass

    def start(self):
        # Spustit vlákno pro přijímání klientů
        pass

class Client:
    def __init__(self, server_address):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(server_address)

    def start(self):
        # Spustit vlákno pro komunikaci s serverem
        pass

# Příklad použití
server_address = ('localhost', 12345)

#server = Server(server_address)
#server.start()

# Čekání na připojení klientů
time.sleep(1)

# #client.start()


class CommModule:
    def __init__(self, socket, timeout_duration=5):
        self.socket = socket
        self.timeout_duration = timeout_duration
        self.lock = threading.Lock()
        self.last_activity_time = time.time()

    def send_frame(self, frame):
        with self.lock:
            # Odeslat rámec přes soket
            self.socket.send(frame.to_bytes())
            self.last_activity_time = time.time()

    def receive_frame(self):
        while True:
            with self.lock:
                if time.time() - self.last_activity_time > self.timeout_duration:
                    # Dosáhnuto timeoutu
                    print("Timeout - spojení se uzavře")
                    return None

            # Přijmout rámec ze soketu
            try:
                data = self.socket.recv(1024)
                if not data:
                    print("Server uzavřel spojení.")
                    return None

                frame = Frame.from_bytes(data)
                self.last_activity_time = time.time()
                return frame

            except socket.timeout:
                pass

    def start(self):
        # Spustit vlákno pro nepřetržitě čtení ze soketu
        threading.Thread(target=self.receive_continuous).start()

    def receive_continuous(self):
        while True:
            frame = self.receive_frame()
            if frame is None:
                break

# Příklad použití
server_address = ('localhost', 12345)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(server_address)
server_socket.listen()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(server_address)

server_comm_module = CommModule(server_socket)
client_comm_module = CommModule(client_socket)

server_comm_module.start()
client_comm_module.start()

# Simulace posílání rámce od klienta ke serveru
client_comm_module.send_frame(IFrame(1, "Hello from client"))

# Simulace posílání odpovědi od serveru ke klientovi
server_comm_module.send_frame(IFrame(2, "Hello from server"))
