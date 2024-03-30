import struct

import acpi


class Frame:
    # třídní proměná pro uchování unikátní id každé instance
    _id = 0
    _instances = []
    _start_byte = acpi.START_BYTE

    def __init__(self, type='Frame'):
        self._header_length = acpi.ACPI_HEADER_LENGTH
        self._total_length = self._header_length
        self._structure = None
        self._type_in_word = type
        self._direction = None

        Frame._id += 1
        self._id = Frame._id
        Frame._instances.append(self)

    def is_structured(self):
        if not self.structure:
            return False
        return True

    @property
    def id(self):
        return self._id

    @property
    def type_in_word(self):
        return self._type_in_word

    @classmethod
    def remove_instance(cls, id=0, instance=None):
        instances_to_remove = []

        for inst in cls._instances:
            if inst._id == id or inst == instance:
                instances_to_remove.append(inst)

        for inst in instances_to_remove:
            cls._instances.remove(inst)

        return instances_to_remove

    @classmethod  # instance s indexem 0 neexistuje ( je rezevrována* )
    def remove_instance(cls, id=0, instance=None):
        if not id:  # zde rezerva*
            if instance:
                cls._instances.remove(instance)
                return True
            else:
                return False

        if id < len(cls._instances):
            del cls._instances[id]
            return True
        else:
            return False

    def get_all_instances(cls):
        return cls._instances

    def serialize(self):
        return False  # it will return false because method is overrided

    @property
    def length(self):
        return self._total_length

    # opravit korektne, toto je spatny vypocet delky!!!
    @length.setter
    def length(self, length):
        self._total_length += length

    def get_length_of_data(self):
        return self._total_length - acpi.ACPI_HEADER_LENGTH

    @property
    def structure(self):
        # here is specify format for each format 
        return self._structure

    @structure.setter
    def structure(self, structure):
        # here is specify format for each format 
        self._structure = structure

    def start_byte(self):
        return self._start_byte

    def __str__(self):
        return f"Typ: {self._type_in_word}, Data in bytes: {self.serialize()}"

    # nepoužito, mám to tu jen pro návod jak dostat data po bytech
    def encode_varint(self, number):
        """Zabalí číslo do varint."""
        encoded_bytes = b""
        while True:
            byte = number & 0xFF
            number >>= 8
            encoded_bytes += struct.pack("B", byte)
            if not number:
                break
        return encoded_bytes

    def decode_varint(self, encoded_bytes):
        """Rozbalí varint na číslo."""
        number = 0
        shift = 0
        for byte in encoded_bytes:
            number |= (byte & 0xFF) << shift
            if not number:
                break
            shift += 8
        return number


@property
def start_byte(self):
    return self._start_byte
