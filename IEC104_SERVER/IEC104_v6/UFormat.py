# -*- coding: utf-8 -*-

import struct

import acpi
from Frame import Frame


class UFormat(Frame):

    def __init__(self, type_frame: int = None, direction='OUT'):
        super().__init__('U-format')
        self.__type_int: int = type_frame
        self.__type_of_Uformat_Str: str = ''
        if type_frame:
            self.type: int = type_frame

        self._direction: str = direction

    @property
    def type(self) -> int:
        return self.__type_int

    @type.setter
    def type(self, type_frame: int) -> None:
        self.__type_int = type_frame
        if type_frame == acpi.STARTDT_ACT:
            self.__type_of_Uformat_Str = 'STARTDT ACT'

        if type_frame == acpi.STARTDT_CON:
            self.__type_of_Uformat_Str = 'STARTDT CON'

        if type_frame == acpi.STOPDT_ACT:
            self.__type_of_Uformat_Str = 'STOPDT ACT'

        if type_frame == acpi.STOPDT_CON:
            self.__type_of_Uformat_Str = 'STOPDT CON'

        if type_frame == acpi.TESTFR_ACT:
            self.__type_of_Uformat_Str = 'TESTDT ACT'

        if type_frame == acpi.TESTFR_CON:
            self.__type_of_Uformat_Str = 'TESTDT CON'

    @property
    def type_of_Uformat_Str(self) -> str:
        return self.__type_of_Uformat_Str

    @property
    def type_int(self) -> int:
        return self.__type_int

    def serialize(self, type_frame: int = None) -> bytes:
        if type_frame:
            self.type = type_frame

        # Doplnění délky do hlavičky
        packet = struct.pack(f"{'B' * (self._header_length + 2)}",
                             Frame.start_byte(),  # start byte
                             self._total_length,  # Total Length pouze hlavička
                             self.__type_int,  # 1. ridici pole
                             0,  # 2. ridici pole
                             0,  # 3. ridici pole
                             0,  # 4. ridici pole
                             )
        self._structure = packet
        return packet

    def __str__(self) -> str:
        return (f"ID: {self.id},"
                f" {self._direction},"
                f" Typ: {self.type_in_word}:"
                f" {self.type_of_Uformat_Str}")
