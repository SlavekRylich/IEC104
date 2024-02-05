import socket
import pickle

class CommModule:
    def __init__(self, socket):
        self.socket = socket

    def send_data(self, data):
        serialized_data = pickle.dumps(data)
        self.socket.sendall(serialized_data)

    def receive_data(self):
        serialized_data = self.socket.recv(1024)
        return pickle.loads(serialized_data)
