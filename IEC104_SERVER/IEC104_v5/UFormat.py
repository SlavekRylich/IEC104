import struct

import acpi
from Frame import Frame


class UFormat(Frame):

    def __init__(self, type_frame=None, direction='OUT'):
        super().__init__('U-format')
        self.__type_int = type_frame
        self.__type_of_Uformat_Str = ''
        if type_frame:
            self.type = type_frame

        self._direction = direction

    @property
    def type(self):
        return self.__type_int

    @type.setter
    def type(self, type_frame):
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
    def type_of_Uformat_Str(self):
        return self.__type_of_Uformat_Str

    @property
    def type_int(self):
        return self.__type_int

    def serialize(self, type_frame=None):
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

    def __str__(self):
        return f"ID: {self.id}, {self._direction} Typ: {self.type_in_word}: {self.type_of_Uformat_Str}"
