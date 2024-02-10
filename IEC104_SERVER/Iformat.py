import math
import struct
from Frame import Frame


class IFormat(Frame):
    
    def __init__(self, data=None, ssn=0, rsn=0):
        super().__init__()
        self.ssn = ssn
        self.rsn = rsn
        self.data = data
        if data != None:
            self.structure()
            
        
    def ssn_increment(self):
        return self.ssn + 1 
    
    def rsn_incremet(self):
        return self.rsn + 1
    
    @property
    def ssn(self):
        return self.ssn
    
    @ssn.setter
    def ssn(self, ssn):
        self.ssn = ssn
    
    @property
    def rsn(self):
        return self.rsn   
    
    @rsn.setter
    def rsn(self, rsn):
        self.rsn = rsn
        
    @property
    def data(self):
        return self.data 
    
    @property
    def set_data_from_structure(self, structure):
        self.data= struct.unpack(f"{'B' * super().get_length_of_data()}", structure)
     
    @property
    def structure(self):
        # here is specify format for each format 
        return self.structure   
    
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
        
        packed_header = struct.pack(f"{'B' * self.length}", 
                                    Frame.Frame.start_byte, # start byte
                                    self.length,  # Total Length pouze hlavička
                                    first,   # 1. ridici pole
                                    second,  # 2. ridici pole
                                    third,   # 3. ridici pole
                                    fourth,  # 4. ridici pole
        )
        self.structure = packed_header + self.data()