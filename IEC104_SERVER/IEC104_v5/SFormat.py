import struct
from Frame import Frame


class SFormat(Frame):
    def __init__(self, rsn=0, direction='OUT'):
        super().__init__('S-format')
        self._rsn = rsn

        self._direction = direction

    def serialize(self, rsn=0):
        if rsn:
            self._rsn = rsn

        # here is specify format for S format
        third = (self._rsn & 0x7F) << 1
        fourth = (self._rsn >> 7) & 0xFF

        # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * (self._header_length + 2)}",
                                    Frame.start_byte,  # start byte
                                    self._total_length,  # Total Length pouze hlavička
                                    1,  # 1. ridici pole
                                    0,  # 2. ridici pole
                                    third,  # 3. ridici pole
                                    fourth,  # 4. ridici pole
                                    )
        self._structure = packed_header
        return self._structure

    @property
    def rsn(self):
        return self._rsn

    @rsn.setter
    def rsn(self, rsn):
        self._rsn = rsn

    def increment_rsn(self):
        self._rsn += 1

    def __str__(self):
        return f"ID: {self.id} {self._direction} Typ: {self.type_in_word}, Data in bytes: {self.serialize()}"
