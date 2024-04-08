from enum import Enum


class ConnectionState(Enum):
    DISCONNECTED: str = 'DISCONNECTED'
    CONNECTED: str = 'CONNECTED'

    def __str__(self) -> str:
        return self.name

    @classmethod
    def set_state(cls, state) -> 'ConnectionState':
        return cls(state)

    def get_state(self):
        return self.value


class TransmissionState(Enum):
    STOPPED = 'STOPPED'
    WAITING_RUNNING = 'WAITING_RUNNING'
    RUNNING = 'RUNNING'
    WAITING_UNCONFIRMED = 'WAITING_UNCONFIRMED'
    WAITING_STOPPED = 'WAITING_STOPPED'

    def __str__(self):
        return self.name

    @classmethod
    def set_state(cls, state):
        return cls(state)

    def get_state(self):
        return self.value

