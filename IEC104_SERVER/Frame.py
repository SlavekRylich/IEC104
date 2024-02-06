import struct
from struct import calcsize
import acpi
import Iformat
import Sformat
import Uformat




class Frame:
    # třídní proměná pro uchování unikátní id každé instance
    _id = 0
    
    def __init__(self):
        self.start_byte = acpi.START_BYTE
        self.length = acpi.ACPI_HEADER_LENGTH
        self.structure = None
        Frame._id += 1  
        self._id = Frame._id
        
    @property
    def id(self):
        return self.id
    
    register_instance(instance)
    
    # prijme paket, zjisti o jaky format se jedna a vytvori odpovidajici instance    
    def parser(self, packet):
        header = self.unpack_header(packet)
        data = 0
    
        if not (header[2] & 1):
            print(f"I format {header[2] & 0xFF}")
            return Iformat(data, 0, 1)
        
        elif (header[2] & 3) == 1:
            print(f"S format {header[2] & 0xFF}")
            return Sformat(0)
        
        elif (header[2] & 3) == 3: 
            print(f"U format {header[2] & 0xFF}")
            return Uformat
        
        else:
            print("Nejaky zpičený format")
            return None  
    
    @property
    def length(self):
        return self.length
    
    # opravit korektne, toto je spatny vypocet delky!!!
    @length.setter
    def length(self):
        self.length += len(self.structure)
    
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
        
    
    def pack(self, first = 0, second = 0, third = 0, fourth = 0, data = 0):
        # Vytvoření binární reprezentace hlavičky IPv4
        packed_header = struct.pack('!BBBBBB', 
                                    self.start_byte, # start byte
                                    0,  # Total Length (bude doplněno později)
                                    0,  # 1. ridici pole
                                    0,  # 2. ridici pole
                                    0,  # 3. ridici pole
                                    0   # 4. ridici pole
        )
        
        
        # Výpočet délky APDU
        if not data:
            total_length = len(packed_header)
            # Doplnění délky do hlavičky
            packed_header = struct.pack(f"{'B' * acpi.ACPI_HEADER_LENGTH}", 
                                        self.start_byte, # start byte
                                        total_length,  # Total Length pouze hlavička
                                        first,   # 1. ridici pole
                                        second,  # 2. ridici pole
                                        third,   # 3. ridici pole
                                        fourth,  # 4. ridici pole
            )
            return packed_header
        
        else:
            packed_data = self.encode_varint(data)
            total_length = len(packed_header) + len(packed_data)

            # Doplnění délky do hlavičky
            packed_header = struct.pack(f"{'B' * acpi.ACPI_HEADER_LENGTH}", 
                                        self.start_byte, # start byte
                                        total_length,  # Total Length i s hlavičkou
                                        first,   # 1. ridici pole
                                        second,  # 2. ridici pole
                                        third,   # 3. ridici pole
                                        fourth,  # 4. ridici pole
            )
        
            return packed_header + packed_data
    
    
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

    
    
