import struct
import Frame


class IFormat(Frame):
    def __init__(self, data, ssn = 0, rsn = 0, ):
        super().__init__(self)
        self.ssn = ssn
        self.rsn = rsn
        self.data = data
        
    def ssn_increment(self):
        return self.ssn + 1 
    
    def rsn_incremetn(self):
        return self.rsn + 1
    
    @property
    def structure(self):
        # here is specify format for I format 
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
        return self.structure
    
    @structure.setter
    def structure(self, value):
        self.structure = value