from abc import ABC, abstractmethod

class CommunicationModuleInterface(ABC):
    @abstractmethod
    def establish_connection(self):
        pass

    @abstractmethod
    def send_data(self, data):
        pass

    @abstractmethod
    def receive_data(self):
        pass

    @abstractmethod
    def close_connection(self):
        pass
