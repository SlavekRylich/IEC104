from Frame import Frame
import struct


class UFormat(Frame):
    def __init__(self):
        super().__init__()
        self.type = None
        
    @property
    def structure(self):
        # here is specify format for each format 
        return self.structure  
    
    @structure.setter
    def structure(self, type): # what type STARTDT, STOPDT, TESTDT
        self.type = type
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * self.length}", 
                                    Frame.Frame.start_byte, # start byte
                                    self.length,  # Total Length pouze hlavička
                                    self.type,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    0,   # 3. ridici pole
                                    0,  # 4. ridici pole
        )
        self.structure = packed_header
        
    @property
    def structure(self):
        return self.structure