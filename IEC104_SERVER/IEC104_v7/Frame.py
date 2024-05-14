# -*- coding: utf-8 -*-

from typing import Any

from apci import APCI


class Frame:
    """
    Class represents a frame.

    Attributes:
    _id (int): Unique identifier for each instance of the class.
    _instances (list): List of all instances of the class.
    _start_byte (int): Start byte value.

    Methods:
    __init__(self, type_frame: str = 'Frame'): Constructor method.
    is_structured(self) -> bool: Checks if the frame is structured.
    serialize(self) -> Any: Serializes the frame data.
    get_length_of_data(self) -> int: Returns the length of the frame data.
    """

    _id: int = 0
    _instances: list['Frame'] = []
    _start_byte: int = APCI.START_BYTE

    def __init__(self, type_frame: str = 'Frame'):
        """
        Constructor method.

        Parameters:
        type_frame (str): Type of the frame. Default is 'Frame'.
        """
        self._header_length: int = APCI.ACPI_HEADER_LENGTH
        self._total_length: int = self._header_length
        self._structure: bytes | None = None
        self._type_in_word: str = type_frame
        self._direction: str | None = None

        Frame._id += 1
        self._id: int = Frame._id
        Frame._instances.append(self)

    def is_structured(self) -> bool:
        """
        Checks if the frame is structured.

        Returns:
        bool: True if the frame is structured, False otherwise.
        """
        if not self.structure:
            return False
        return True

    @property
    def id(self) -> int:
        """
        Returns the unique identifier of the frame.

        Returns:
        int: Unique identifier of the frame.
        """
        return self._id

    @property
    def type_in_word(self) -> str:
        """
        Returns the type of the frame.

        Returns:
        str: Type of the frame.
        """
        return self._type_in_word

    @classmethod
    def get_all_instances(cls) -> list:
        """
        Returns all instances of the Frame class.

        Returns:
        list: List of all instances of the Frame class.
        """
        return cls._instances

    def serialize(self) -> Any:
        """
        Serializes the frame data.

        Returns:
        Any: Serialized frame data.
        """
        pass

    @property
    def length(self) -> int:
        """
        Returns the total length of the frame.

        Returns:
        int: Total length of the frame.
        """
        return self._total_length

    @length.setter
    def length(self, length):
        """
        Sets the total length of the frame.

        Parameters:
        length (int): New total length of the frame.
        """
        self._total_length += length

    def get_length_of_data(self) -> int:
        """
        Returns the length of the frame data.

        Returns:
        int: Length of the frame data.
        """
        return self._total_length - APCI.ACPI_HEADER_LENGTH

    @property
    def structure(self) -> bytes:
        """
        Returns the structure of the frame.

        Returns:
        bytes: Structure of the frame.
        """
        return self._structure

    @structure.setter
    def structure(self, structure) -> None:
        """
        Sets the structure of the frame.

        Parameters:
        structure (bytes): New structure of the frame.
        """
        self._structure = structure

    @classmethod
    def start_byte(cls) -> int:
        """
        Returns the start byte value.

        Returns:
        int: Start byte value.
        """
        return APCI.START_BYTE

    def __str__(self) -> str:
        """
        Returns a string representation of the frame.

        Returns:
        str: String representation of the frame.
        """
        return f"Typ: {self._type_in_word}, Data in bytes: {self.serialize()}"
