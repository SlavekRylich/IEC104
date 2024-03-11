import struct

import acpi



class Frame:
# třídní proměná pro uchování unikátní id každé instance
    _id = 0
    _instances = []
    __start_byte = acpi.START_BYTE

    def __init__(self, type='Frame'):
        self.__header_length = acpi.ACPI_HEADER_LENGTH
        self.__total_length = self.__header_length
        self.__structure = None
        self.__type_in_word = type
        Frame._id += 1
        self._id = Frame._id
        Frame._instances.append(self)
        
    def is_structured(self):
        if not self.__structure:
            return False
        return True
    
    @property
    def get_id(self):
        return self._id
    
    @property
    def __type_in_word(self):
         return self.__type_in_word

    @classmethod
    def remove_instance(cls, id = 0, instance = None):
        instances_to_remove = []
        
        for inst in cls._instances:
            if inst._id == id or inst == instance:
                instances_to_remove.append(inst)

        for inst in instances_to_remove:
            cls._instances.remove(inst)

        return instances_to_remove

    @classmethod        # instance s indexem 0 neexistuje ( je rezevrována* )
    def remove_instance(cls, id = 0, instance = None):
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
        return False    # it will return false because method is overrided
        
    @property
    def length(self):
        return self.__total_length

    # opravit korektne, toto je spatny vypocet delky!!!
    @length.setter
    def length(self, length):
        self.__total_length += length

        
    def get_length_of_data(self):
        return self.__total_length - acpi.ACPI_HEADER_LENGTH

    
    @property 
    def __structure(self):
        # here is specify format for each format 
        return self.__structure
    
    @__structure.setter 
    def __structure(self, structure):
        # here is specify format for each format 
        self.__structure = structure


    def __str__(self):
        return f"Typ: {self.__type_in_word}, Data in bytes: {self.serialize()}"



    # nepoužito, mám to tu jen pro návod jak dostat data po bytech 
    def encode_varint(self,number):
        """Zabalí číslo do varint."""
        encoded_bytes = b""
        while True:
            byte = number & 0xFF
            number >>= 8
            encoded_bytes += struct.pack("B", byte)
            if not number:
                break
        return encoded_bytes

    def decode_varint(self,encoded_bytes):
        """Rozbalí varint na číslo."""
        number = 0
        shift = 0
        for byte in encoded_bytes:
            number |= (byte & 0xFF) << shift
            if not number:
                break
            shift += 8
        return number



