import math
import struct
from Frame import Frame


class IFormat(Frame):
    class_ssn = 0
    class_rsn = 0
    
    
    def __init__(self, data=None, ssn=0, rsn=0):
        super().__init__()
        self.ssn = ssn
        self.rsn = rsn
        self.data = data
        if data != None:
            self.structure(self.data)
    
    # třídní atributy pro číslování rámců (dořešit v budoucnu)        
     #property
    def get_class_ssn(cls):
        return cls.class_ssn
    
     #class_ssn.setter
    def set_class_ssn(cls, ssn):
        cls.class_ssn = ssn
    
     #property
    def get_class_rsn(cls):
        return cls.class_rsn
    
     #class_rsn.setter
    def set_class_rsn(cls, rsn):
        cls.class_rsn = rsn
    
    def ssn_increment(self):
        return self.ssn + 1 
    
    def rsn_incremet(self):
        return self.rsn + 1
    
     #property
    def get_ssn(self):
        return self.ssn
    
     #ssn.setter
    def set_ssn(self, ssn):
        self.ssn = ssn
    
     #property
    def get_rsn(self):
        return self.rsn   
    
     #rsn.setter
    def set_rsn(self, rsn):
        self.rsn = rsn
        
     #property
    def get_data(self):
        return self.data 
    
     #property
    def set_data_from_structure(self, structure):
        self.data= struct.unpack(f"{'B' * super().get_length_of_data()}", structure)
     
     #property
    def get_structure(self):
        # here is specify format for each format 
        return self.structure   
    
     #structure.setter
    def set_structure(self, data):
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
        self.length += math.ceil(len(data) / 8)
        
        packed_header = struct.pack(f"{'B' * self.length + 2}", 
                                    Frame.start_byte, # start byte
                                    self.length,  # Total Length pouze hlavička
                                    first,   # 1. ridici pole
                                    second,  # 2. ridici pole
                                    third,   # 3. ridici pole
                                    fourth,  # 4. ridici pole
        )
        self.structure = packed_header + data