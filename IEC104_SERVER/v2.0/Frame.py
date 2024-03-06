import struct

import acpi



class Frame:
# třídní proměná pro uchování unikátní id každé instance
    _id = 0
    instances = []
    start_byte = acpi.START_BYTE

    def __init__(self, type='Frame'):
        self.header_length = acpi.ACPI_HEADER_LENGTH
        self.total_length = self.header_length
        self.structure = None
        self.type_in_word = type
        Frame._id += 1
        self._id = Frame._id
        Frame.instances.append(self)
        
    def is_structured(self):
        if not self.structure:
            return False
        return True
        
    def get_id(self):
        return self._id
    
    def get_type_in_word(self):
         return self.type_in_word

    @classmethod
    def remove_instance(cls, id = 0, instance = None):
        instances_to_remove = []
        
        for inst in cls.instances:
            if inst._id == id or inst == instance:
                instances_to_remove.append(inst)

        for inst in instances_to_remove:
            cls.instances.remove(inst)

        return instances_to_remove

    @classmethod        # instance s indexem 0 neexistuje ( je rezevrována* )
    def remove_instance(cls, id = 0, instance = None):
        if not id:  # zde rezerva*
            if instance: 
                cls.instances.remove(instance)
                return True
            else:
                return False
        
        if id < len(cls.instances):
            del cls.instances[id]
            return True
        else:
            return False
        
    def get_all_instances(cls):
        return cls.instances

    def serialize(self):
        return False    # it will return false because method is overrided
        
            
    def get_length(self):
        return self.total_length

    # opravit korektne, toto je spatny vypocet delky!!!
        #length.setter
    def set_length(self, length):
        self.total_length += length

        
    def get_length_of_data(self):
        return self.total_length - acpi.ACPI_HEADER_LENGTH

    # vraci strukturu ramce
        
    def get_structure(self):
        # here is specify format for each format 
        return self.structure

        #structure.deleter
    def rem_structure(self):
        del self.structure

    def __str__(self):
        return f"Typ: {self.type_in_word}, Data in bytes: {self.serialize()}"



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



