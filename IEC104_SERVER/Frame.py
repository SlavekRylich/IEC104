import struct
from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat
import acpi



class Frame:
# třídní proměná pro uchování unikátní id každé instance
    _id = 0
    instances = []
    start_byte = acpi.START_BYTE

    def __init__(self):
        self.total_length = acpi.ACPI_HEADER_LENGTH
        self.structure = None
        Frame._id += 1
        self._id = Frame._id
        Frame.instances.append(self)
        
    def is_structured(self):
        if not self.structure:
            return False
        return True
        
    def get_id(self):
        return self._id

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
        
    # předpokládám APDU = ACPI + ASDU, již bez start bytu a length
    @classmethod
    def parser(cls, apdu, length): 
        
        unpacked_apdu = struct.unpack(f"{'B' * (length)}", apdu)
        
                    
        frame_format = cls.what_format(unpacked_apdu)    
            
        if frame_format == "I":
            
            ssn = (unpacked_apdu[1] << 7) + (unpacked_apdu[0] >> 1) 
            rsn = (unpacked_apdu[3] << 7) + (unpacked_apdu[2] >> 1)
            data = struct.unpack(f"{'B' * (length)}", apdu)
            asdu_data = data[acpi.ACPI_HEADER_LENGTH:]
            
            # vytvoreni nove instance Iformatu a vlozeni do bufferu
            new_instance = IFormat(asdu_data, ssn, rsn)
            # self.buffer_recv_I_frames.append(new_instance)
            # self.buffer_recv_all_frames.append(new_instance)
            
            return (0, new_instance)
            
        elif frame_format == "S":
            
            rsn = (unpacked_apdu[3] << 7) + (unpacked_apdu[2] >> 1)
            
            new_instance = SFormat(rsn)
            # self.buffer_recv_S_frames.append(new_instance)
            # self.buffer_recv_all_frames.append(new_instance)
        
            # kód označující že byl proveden S format
            return (1, new_instance)
            
        elif frame_format == "U":
            first_byte = unpacked_apdu[0]
            
            new_instance = UFormat()
            
            # STARTDT ACT
            if first_byte == acpi.STARTDT_ACT:
                
                new_instance.set_structure(acpi.STARTDT_ACT)
                
                # self.buffer_recv_U_frames.append(new_instance)
                # self.buffer_recv_all_frames.append(new_instance)
                return (2, new_instance)
                new_instance = UFormat()
                new_instance.set_structure(acpi.STARTDT_CON)
                
                
                
            # STOPDT ACT
            elif first_byte == acpi.STOPDT_ACT:
                
                new_instance.set_structure(acpi.STOPDT_ACT)
                
                # self.buffer_recv_U_frames.append(new_instance)
                # self.buffer_recv_all_frames.append(new_instance)
                return (3, new_instance)
                new_instance = UFormat()
                new_instance.set_structure(acpi.STOPDT_CON)
                
                
            
            # TESTDT ACT
            elif first_byte == acpi.TESTFR_ACT:
                
                new_instance.set_structure(acpi.TESTFR_ACT)
                
                # self.buffer_recv_U_frames.append(new_instance)
                # self.buffer_recv_all_frames.append(new_instance)
                return (4, new_instance)
                new_instance = UFormat()
                new_instance.set_structure(acpi.TESTFR_CON)
                
            
            else:
                # nemělo by nikdy nastat           
                return  5
        
        else:
            raise Exception("Přijat neznámí formát")

    @classmethod  
    def what_format(cls, first_byte):
        first_byte = first_byte[0]
        
        if not (first_byte & 1):
            # print(f"I format {first_byte & 0xFF}")
            return "I"
        elif (first_byte & 3) == 1:
            # print(f"S format {first_byte & 0xFF}")
            return "S"
        elif (first_byte & 3) == 3: 
            # print(f"U format {first_byte & 0xFF}")
            return "U"
        else:
            # print("Nejaky zpičený format")
            return None

        
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


        #structure.setter
    def set_structure(self, value):
        self.structure = value
        
        #structure.deleter
    def rem_structure(self):
        del self.structure




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



