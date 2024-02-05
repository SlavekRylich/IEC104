from abc import ABC, abstractmethod

class FrameInterface(ABC):
    @abstractmethod
    def build_frame(self, apdu_data):
        pass

    @abstractmethod
    def parse_frame(self, frame):
        pass
