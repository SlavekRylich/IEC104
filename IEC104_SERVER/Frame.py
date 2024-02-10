import struct
from struct import calcsize
import acpi



class Frame:
    # třídní proměná pro uchování unikátní id každé instance
    _id = 0
    instances = []
    start_byte = acpi.START_BYTE
    
    def __init__(self):
        self.length = acpi.ACPI_HEADER_LENGTH
        self.structure = None
        Frame._id += 1
        self._id = Frame._id
        Frame.instances.append(self)
        
    @property
    def id(self):
        return self.id
    
    @property
    def get_all_instances(cls):
        return Frame.instances
    
    # prijme paket, zjisti o jaky format se jedna a vytvori odpovidajici instance    
    def parser(self, packet):
        header = self.unpack_header(packet)
        data = 0
    
        if not (header[2] & 1):
            print(f"I format {header[2] & 0xFF}")
            return IFormat(data, 0, 1)
        
        elif (header[2] & 3) == 1:
            print(f"S format {header[2] & 0xFF}")
            return SFormat(0)
        
        elif (header[2] & 3) == 3: 
            print(f"U format {header[2] & 0xFF}")
            return UFormat()
        
        else:
            print("Nejaky zpičený format")
            return None  
    
    @property
    def length(self):
        return self.length
    
    # opravit korektne, toto je spatny vypocet delky!!!
    @length.setter
    def length(self, length):
        self.length += length
    
    @property
    def get_length_of_data(self):
        return self.length - acpi.ACPI_HEADER_LENGTH
    
    # vraci strukturu ramce
    @property
    def structure(self):
        # here is specify format for each format 
        return self.structure
    
    
    @structure.setter
    def structure(self, value):
        self.structure = value
        
    @structure.deleter
    def structure(self):
        del self.structure
    
    
    def unpack_header(self, packed_header, length):
        
        unpacked_header = struct.unpack(f"{'B' * length}", packed_header)        
        header = unpacked_header
        
        return header
    
    
    def unpack_data(self, packed_data, length):
        # Získání hodnot z tuple
        print(len(packed_data))
        
        unpacked_data = self.decode_varint(packed_data)
        print(unpacked_data)        
        data = unpacked_data
        
        return data
    
    
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

    
    
