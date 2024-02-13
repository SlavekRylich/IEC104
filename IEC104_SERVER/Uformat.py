from Frame import Frame
import struct


class UFormat(Frame):
    def __init__(self):
        super().__init__()
        self.type = None
        
    #property
    def get_type(self):
        return self.type 
    
    def set_type(self, type):
        self.type = type 
    
    #serializace
    def set_structure(self, type): # what type STARTDT, STOPDT, TESTDT
        self.type = type
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * (self.length + 2)}", 
                                    Frame.start_byte, # start byte
                                    self.length,  # Total Length pouze hlavička
                                    self.type,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    0,   # 3. ridici pole
                                    0,  # 4. ridici pole
        )
        self.structure = packed_header
    
    def serialize(self, type=0):
        if type:
            self.type = type
        
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * (self.length + 2)}", 
                                    Frame.start_byte, # start byte
                                    self.length,  # Total Length pouze hlavička
                                    self.type,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    0,   # 3. ridici pole
                                    0,  # 4. ridici pole
        )
        self.structure = packed_header
        return packed_header
    
    def deserialize(self, apdu):
        receive_packet = struct.unpack(f"{'B' * 2}", receive_packet)
        if type:
            self.type = type
        
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * (self.length + 2)}", 
                                    Frame.start_byte, # start byte
                                    self.length,  # Total Length pouze hlavička
                                    self.type,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    0,   # 3. ridici pole
                                    0,  # 4. ridici pole
        )
        self.structure = packed_header
        return packed_header
    