# -*- coding: utf-8 -*-

from enum import Enum


class ConnectionState(Enum):
    """
    Enum representing the connection state of a system.

    Attributes:
    DISCONNECTED: Represents the disconnected state.
    CONNECTED: Represents the connected state.
    """
    DISCONNECTED: str = 'DISCONNECTED'
    CONNECTED: str = 'CONNECTED'

    def __str__(self) -> str:
        """
        Returns the name of the connection state.

        Returns:
        str: The name of the connection state.
        """
        return self.name

    @classmethod
    def set_state(cls, state: str):
        """
        Sets the connection state based on the given string.

        Args:
        state (str): The string representation of the connection state.

        Returns:
        ConnectionState: The corresponding ConnectionState enum value.
        """
        return cls(state)

    def get_state(self) -> str:
        """
        Returns the string representation of the connection state.

        Returns:
        str: The string representation of the connection state.
        """
        return self.value


class TransmissionState(Enum):
    """
    Enum representing the transmission state of a system.

    Attributes:
    STOPPED: Represents the stopped state.
    WAITING_RUNNING: Represents the waiting running state.
    RUNNING: Represents the running state.
    WAITING_UNCONFIRMED: Represents the waiting unconfirmed state.
    WAITING_STOPPED: Represents the waiting stopped state.
    """
    STOPPED: str = 'STOPPED'
    WAITING_RUNNING: str = 'WAITING_RUNNING'
    RUNNING: str = 'RUNNING'
    WAITING_UNCONFIRMED: str = 'WAITING_UNCONFIRMED'
    WAITING_STOPPED: str = 'WAITING_STOPPED'

    def __str__(self) -> str:
        """
        Returns the name of the transmission state.

        Returns:
        str: The name of the transmission state.
        """
        return self.name

    @classmethod
    def set_state(cls, state: str):
        """
        Sets the transmission state based on the given string.

        Args:
        state (str): The string representation of the transmission state.

        Returns:
        TransmissionState: The corresponding TransmissionState enum value.
        """
        return cls(state)

    def get_state(self) -> str:
        """
        Returns the string representation of the transmission state.

        Returns:
        str: The string representation of the transmission state.
        """
        return self.value
