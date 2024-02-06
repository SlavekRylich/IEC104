import math
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
    
    
    @structure.setter
    def structure(self):
        # here is specify format for S format
        first = 0
        second = 0
        third = 0
        fourth = 0
        first |= (self.ssn & 0x7F) << 1
        second |= (self.ssn >> 7) & 0xFF
        third |= (self.rsn & 0x7F) << 1
        fourth |= (self.rsn >> 7) & 0xFF
        
        # zaokrouhlední dat na celé byty
        self.length += math.ceil(len(self.data) / 8)
        
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * self.length}", 
                                    self.start_byte, # start byte
                                    self.length,  # Total Length pouze hlavička
                                    first,   # 1. ridici pole
                                    second,  # 2. ridici pole
                                    third,   # 3. ridici pole
                                    fourth,  # 4. ridici pole
        )
        self.structure = packed_header