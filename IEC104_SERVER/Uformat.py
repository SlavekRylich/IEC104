import Frame
import struct


class UFormat(Frame):
    def __init__(self):
        super().__init__(self)
        self.type = None
        
    @property
    def structure(self, type):
        # here is specify format for U format
        
        return self.structure
    
    @structure.setter
    def structure(self, type): # what type STARTDT, STOPDT, TESTDT
        self.type = type
        total_length = self.length
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * self.length}", 
                                    self.start_byte, # start byte
                                    total_length,  # Total Length pouze hlavička
                                    self.type,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    0,   # 3. ridici pole
                                    0,  # 4. ridici pole
        )
        self.structure = packed_header
        
    @property
    def structure(self):
        return 