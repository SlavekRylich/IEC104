from abc import ABC, abstractmethod

class ClientServerInterface(ABC):
    @abstractmethod
    def send_apdu(self, data):
        pass

    @abstractmethod
    def receive_apdu(self):
        pass
