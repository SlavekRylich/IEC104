from Frame import Frame
import struct


class UFormat(Frame):
    def __init__(self, type = None):
        super().__init__()
        self.type = type
        
    #property
    def get_type(self):
        return self.type 
    
    def set_type(self, type):
        self.type = type 
        
    
    
    #serializace
    def set_structure(self, type = None): # what type STARTDT, STOPDT, TESTDT
        if type:
            self.type = type
        
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * (self.total_length + 2)}", 
                                    Frame.start_byte, # start byte
                                    self.total_length,  # Total Length pouze hlavička
                                    self.type,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    0,   # 3. ridici pole
                                    0,  # 4. ridici pole
        )
        self.structure = packed_header
    
    # serializace dat 
    def serialize(self, type = None):
        if type:
            self.type = type
        
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * (self.total_length + 2)}", 
                                    Frame.start_byte, # start byte
                                    self.total_length,  # Total Length pouze hlavička
                                    self.type,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    0,   # 3. ridici pole
                                    0,  # 4. ridici pole
        )
        self.structure = packed_header
        return packed_header
    
    
    