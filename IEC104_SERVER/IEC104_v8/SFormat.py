# -*- coding: utf-8 -*-

import struct

from Frame import Frame


class SFormat(Frame):
    """
    SFormat class represents a specific type of IEC104 frame.
    It inherits from the Frame class and provides methods for serializing the frame
    and managing the RSN (Receive Sequence Number) field.
    """
    def __init__(self, rsn: int = 0, direction: str = 'OUT'):
        """
        Initialize a new SFormat instance.

        :param rsn: The initial Receive Sequence Number (default is 0).
        :param direction: The direction of the frame ('OUT' or 'IN' - default is 'OUT').
        """
        super().__init__('S-format')
        self._rsn: int = rsn
        self._direction: str = direction

    def serialize(self, rsn: int = 0) -> bytes:
        """
        Serialize the SFormat frame into bytes.

        :param rsn: The Request Sequence Number to be used for serialization. If not provided, the current RSN will be used.
        :return: The serialized frame as bytes.
        """
        if rsn:
            self._rsn = rsn

        third = (self._rsn & 0x7F) << 1
        fourth = (self._rsn >> 7) & 0xFF

        packed_header = struct.pack(f"{'B' * (self._header_length + 2)}",
                                    Frame.start_byte(),  # start byte
                                    self._total_length,  # Total Length pouze hlavička
                                    1,  # 1. ridici pole
                                    0,  # 2. ridici pole
                                    third,  # 3. ridici pole
                                    fourth,  # 4. ridici pole
                                    )
        self._structure = packed_header
        return self._structure

    @property
    def rsn(self) -> int:
        """
        Get the current Receive Sequence Number.

        :return: The current RSN.
        """
        return self._rsn

    @rsn.setter
    def rsn(self, rsn: int) -> None:
        """
        Set the Receive Sequence Number.

        :param rsn: The new RSN value.
        """
        self._rsn = rsn

    def __str__(self) -> str:
        """
        Get a string representation of the SFormat frame.

        :return: The string representation of the frame.
        """
        return (f"ID: {self.id},"
                f" {self._direction},"
                f" Typ: {self.type_in_word},"
                f" Data in bytes: {self.serialize()}")
