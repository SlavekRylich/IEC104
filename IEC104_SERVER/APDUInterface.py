from abc import ABC, abstractmethod

class APDUInterface(ABC):
    @abstractmethod
    def build_apdu(self, data):
        pass

    @abstractmethod
    def parse_apdu(self, apdu):
        pass
