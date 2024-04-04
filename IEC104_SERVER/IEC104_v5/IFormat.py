import struct
# TypeError: module() takes at most 2 arguments (3 given)
# Your error is happening because Object is a module, not a class. 
# So your inheritance is screwy.
# Change your import statement to:
# from Object import ClassName
from Frame import Frame


class IFormat(Frame):
    __class_ssn = 0
    __class_rsn = 0

    def __init__(self, data, ssn=0, rsn=0, direction='OUT'):
        super().__init__('I-format')
        self.__ssn = ssn
        self.__rsn = rsn
        self.__data = data
        self.__data_length = self.get_length_of_data()
        # zaokrouhlední dat na celé byty
        self._total_length += self.__data_length

        self._direction = direction

    # třídní atributy pro číslování rámců (dořešit v budoucnu)      
    # už nevím proč, nejspíš pokud bych to neřešil tak, že co packet to instance X formátu ?
    @classmethod
    def get_class_ssn(cls):
        return cls.__class_ssn

    @classmethod
    def set_class_ssn(cls, ssn):
        cls.__class_ssn = ssn

    @classmethod
    def get_class_rsn(cls):
        return cls.__class_rsn

    @classmethod
    def set_class_rsn(cls, rsn):
        cls.__class_rsn = rsn

    @property
    def ssn(self):
        return self.__ssn

    @ssn.setter
    def ssn(self, ssn):
        self.__ssn = ssn

    @property
    def rsn(self):
        return self.__rsn

    @rsn.setter
    def rsn(self, rsn):
        self.__rsn = rsn

    @property
    def data(self):
        return self.__data

    def get_length_of_data(self):
        return len(self.__data)

    def set_data_from_structure(self, structure):
        self.__data = struct.unpack(f"{'B' * super().get_length_of_data()}", structure)

    def structure(self):
        # here is specify format for each format 
        return self._structure

    def serialize(self):
        # here is specify format for I format
        first = (self.__ssn & 0x7F) << 1
        second = (self.__ssn >> 7) & 0xFF
        third = (self.__rsn & 0x7F) << 1
        fourth = (self.__rsn >> 7) & 0xFF

        # + 2 because start_byte and length
        packed_header = struct.pack(f"{'B' * (self._header_length + 2)}",
                                    Frame.start_byte(),  # start byte
                                    self._total_length,  # Total Length pouze hlavička
                                    first,  # 1. ridici pole
                                    second,  # 2. ridici pole
                                    third,  # 3. ridici pole
                                    fourth,  # 4. ridici pole
                                    )

        # zabali random data
        # packet_data = struct.pack(f"{'B' * self.data_length}", self.data)

        if type(self.__data) is tuple:
            data = struct.pack('I' * len(self.__data), *self.__data)
            self._structure = packed_header + data
            return self._structure

        # self.structure = packed_header + packet_data
        self._structure = packed_header + self.__data
        return self._structure

    def __str__(self):
        return (f"ID: {self.id},"
                f" {self._direction},"
                f" Typ: {self.type_in_word},"
                f" Data in bytes: {self.serialize()[:4]}...")

