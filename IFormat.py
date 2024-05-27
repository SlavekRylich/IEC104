# -*- coding: utf-8 -*-

import struct
from typing import Any

# TypeError: module() takes at most 2 arguments (3 given)
# Your error is happening because Object is a module, not a class. 
# So your inheritance is screwy.
# Change your import statement to:
# from Object import ClassName
from Frame import Frame


class IFormat(Frame):
    """
    IFormat class represents a specific format of data packet.
    It inherits from the Frame class.
    """

    def __init__(self, data: bytes, ssn: int = 0, rsn: int = 0, direction: str = 'OUT'):
        """
        Initialize IFormat object.

        Parameters:
        data (bytes): Data to be included in the packet.
        ssn (int): Sequence number for sender.
        rsn (int): Sequence number for receiver.
        direction (str): Direction of the packet (default is 'OUT').
        """
        super().__init__('I-format')
        self.__ssn: int = ssn
        self.__rsn: int = rsn
        self.__data: bytes = data
        self.__data_length: int = len(data)
        self._direction: str = direction

    @property
    def ssn(self) -> int:
        """
        Get the SSN.

        Returns:
        int: SSN.
        """
        return self.__ssn

    @ssn.setter
    def ssn(self, ssn: int) -> None:
        """
        Set the SSN.

        Parameters:
        ssn (int): New value for SSN.
        """
        self.__ssn = ssn

    @property
    def rsn(self) -> int:
        """
        Get the RSN.

        Returns:
        int: RSN.
        """
        return self.__rsn

    @rsn.setter
    def rsn(self, rsn: int) -> None:
        """
        Set the RSN.

        Parameters:
        rsn (int): New value for RSN.
        """
        self.__rsn = rsn

    @property
    def data(self) -> bytes:
        """
        Get the data.

        Returns:
        bytes: Data.
        """
        return self.__data

    @property
    def length(self) -> int:
        """
        Get the total length of the packet.

        Returns:
        int: Total length of the packet.
        """
        return self._total_length + self.__data_length

    def get_length_of_data(self) -> int:
        """
        Get the length of the data.

        Returns:
        int: Length of the data.
        """
        return len(self.__data)

    def set_data_from_structure(self, structure) -> None:
        """
        Set the data from a given structure.

        Parameters:
        structure: Structure from which to extract data.
        """
        self.__data = struct.unpack(f"{'B' * super().get_length_of_data()}", structure)

    def structure(self) -> bytes:
        """
        Get the structure of the packet.

        Returns:
        bytes: Structure of the packet.
        """
        return self._structure

    def serialize(self) -> bytes | Any:
        """
        Serialize the packet into bytes.

        Returns:
        bytes: Serialized packet.
        """
        first = (self.__ssn & 0x7F) << 1
        second = (self.__ssn >> 7) & 0xFF
        third = (self.__rsn & 0x7F) << 1
        fourth = (self.__rsn >> 7) & 0xFF

        # + 2 because start_byte and length
        packed_header = struct.pack(f"{'B' * (self._header_length + 2)}",
                                    Frame.start_byte(),  # start byte
                                    self.length,  # Total Length pouze hlavička
                                    first,  # 1. ridici pole
                                    second,  # 2. ridici pole
                                    third,  # 3. ridici pole
                                    fourth,  # 4. ridici pole
                                    )

        # packet_data = struct.pack(f"{'B' * self.data_length}", self.data)

        if type(self.__data) is tuple:
            data = struct.pack('I' * len(self.__data), *self.__data)
            self._structure = packed_header + data
            return self._structure

        # self.structure = packed_header + packet_data
        self._structure = packed_header + self.__data
        return self._structure

    def __str__(self) -> str:
        """
        Get a string representation of the packet.

        Returns:
        str: String representation of the packet.
        """
        return (f"ID: {self.id},"
                f" {self._direction},"
                f" Typ: {self.type_in_word},"
                f" Data in bytes: {self.serialize()[:4]}...")
