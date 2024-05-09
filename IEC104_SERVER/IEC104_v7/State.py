# -*- coding: utf-8 -*-

from enum import Enum


class ConnectionState(Enum):
    DISCONNECTED: str = 'DISCONNECTED'
    CONNECTED: str = 'CONNECTED'

    def __str__(self) -> str:
        return self.name

    @classmethod
    def set_state(cls, state: str):
        return cls(state)

    def get_state(self) -> str:
        return self.value


class TransmissionState(Enum):
    STOPPED: str = 'STOPPED'
    WAITING_RUNNING: str = 'WAITING_RUNNING'
    RUNNING: str = 'RUNNING'
    WAITING_UNCONFIRMED: str = 'WAITING_UNCONFIRMED'
    WAITING_STOPPED: str = 'WAITING_STOPPED'

    def __str__(self) -> str:
        return self.name

    @classmethod
    def set_state(cls, state: str):
        return cls(state)

    def get_state(self) -> str:
        return self.value
