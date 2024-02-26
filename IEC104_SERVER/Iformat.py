import math
import struct
# TypeError: module() takes at most 2 arguments (3 given)
# Your error is happening because Object is a module, not a class. 
# So your inheritance is screwy.
#Change your import statement to:
#from Object import ClassName
from Frame import Frame


class IFormat(Frame):
    class_ssn = 0
    class_rsn = 0
    
    def __init__(self, data, ssn=0, rsn=0):
        super().__init__('I-format')
        self.ssn = ssn
        self.rsn = rsn
        self.data = data
        self.data_length = self.get_length_of_data()
        # zaokrouhlední dat na celé byty
        self.total_length += self.data_length
    
    # třídní atributy pro číslování rámců (dořešit v budoucnu)      
     # už nevím proč, nejspíš pokud bych to neřešil tak, že co packet to instance X formátu ?  
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
    
    def get_length_of_data(self):
        return len(self.data)
    
     #property
    def set_data_from_structure(self, structure):
        self.data= struct.unpack(f"{'B' * super().get_length_of_data()}", structure)
     
     #property
    def get_structure(self):
        # here is specify format for each format 
        return self.structure   
    
        
    def serialize(self):
    # here is specify format for I format
        first = (self.ssn & 0x7F) << 1
        second = (self.ssn >> 7) & 0xFF
        third = (self.rsn & 0x7F) << 1
        fourth = (self.rsn >> 7) & 0xFF
        
        
        # + 2 because start_byte and length
        packed_header = struct.pack(f"{'B' * (self.header_length + 2)}", 
                                    Frame.start_byte, # start byte
                                    self.total_length,  # Total Length pouze hlavička
                                    first,   # 1. ridici pole
                                    second,  # 2. ridici pole
                                    third,   # 3. ridici pole
                                    fourth,  # 4. ridici pole
        )
        
        # zabali random data
        #packet_data = struct.pack(f"{'B' * self.data_length}", self.data)
        
        if type(self.data) == tuple:
            data = struct.pack('I' * len(self.data), *self.data)
            self.structure = packed_header + data
            return self.structure
        
        #self.structure = packed_header + packet_data
        self.structure = packed_header + self.data
        return self.structure
    
    def __str__(self):
        return f"Typ: {self.type_in_word}, Data in bytes: {self.serialize()}"