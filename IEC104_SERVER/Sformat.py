from Frame import Frame
import struct


class SFormat(Frame):
    def __init__(self, rsn = 0):
        super().__init__()
        self.rsn = rsn
    
        
     #structure.setter
    def set_structure(self, rsn = 0):
        
        if rsn:
            self.rsn = rsn
        
        # here is specify format for S format
        third = 0
        fourth = 0
        third |= (self.rsn & 0x7F) << 1
        fourth |= (self.rsn >> 7) & 0xFF
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * self.total_length + 2}", 
                                    Frame.start_byte, # start byte
                                    self.total_length,  # Total Length pouze hlavička
                                    1,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    third,   # 3. ridici pole
                                    fourth,  # 4. ridici pole
        )
        self.structure = packed_header
    
    def serialize(self, rsn = 0):
        
        if rsn:
            self.rsn = rsn
        
        # here is specify format for S format
        third = (self.rsn & 0x7F) << 1
        fourth = (self.rsn >> 7) & 0xFF
        
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * self.total_length + 2}", 
                                    Frame.start_byte, # start byte
                                    self.total_length,  # Total Length pouze hlavička
                                    1,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    third,   # 3. ridici pole
                                    fourth,  # 4. ridici pole
        )
        self.structure = packed_header
        return self.structure
    
     
     #property
    def get_rsn(self):
        return self.rsn
            
    
     #rsn.setter
    def set_rsn(self, rsn):
        self.rsn = rsn
        
    def increment_rsn(self):
        self.rsn += 1
        
        
    
    
