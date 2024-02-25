import Frame
import struct
import acpi

from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat

class Parser:
    
    def parser(apdu, length): 
        
        unpacked_apdu = struct.unpack(f"{'B' * (length)}", apdu)
        
                    
        frame_format = Parser.what_format(unpacked_apdu)    
        
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
                
                new_instance.set_type(acpi.STARTDT_ACT)
                
                # self.buffer_recv_U_frames.append(new_instance)
                # self.buffer_recv_all_frames.append(new_instance)
                return (2, new_instance)
                new_instance = UFormat()
                new_instance.set_structure(acpi.STARTDT_CON)
                
                
                
            # STOPDT ACT
            elif first_byte == acpi.STOPDT_ACT:
                
                new_instance.set_type(acpi.STOPDT_ACT)
                
                # self.buffer_recv_U_frames.append(new_instance)
                # self.buffer_recv_all_frames.append(new_instance)
                return (3, new_instance)
                new_instance = UFormat()
                new_instance.set_structure(acpi.STOPDT_CON)
                
                
            
            # TESTDT ACT
            elif first_byte == acpi.TESTFR_ACT:
                
                new_instance.set_type(acpi.TESTFR_ACT)
                
                # self.buffer_recv_U_frames.append(new_instance)
                # self.buffer_recv_all_frames.append(new_instance)
                return (4, new_instance)
                new_instance = UFormat()
                new_instance.set_structure(acpi.TESTFR_CON)
            
            elif first_byte == acpi.STARTDT_CON:
                new_instance.set_type(acpi.STARTDT_CON)
                return (5, new_instance)
            # STOPDT ACT
            elif first_byte == acpi.STOPDT_CON:
                
                new_instance.set_type(acpi.STOPDT_CON)
                return (6, new_instance)
            # TESTDT ACT
            elif first_byte == acpi.TESTFR_CON:
                new_instance.set_type(acpi.TESTFR_CON)
                return (7, new_instance)
            
            else:
                # nemělo by nikdy nastat           
                return  8
        
        else:
            raise Exception("Přijat neznámí formát")

    def what_format(first_byte):
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
        