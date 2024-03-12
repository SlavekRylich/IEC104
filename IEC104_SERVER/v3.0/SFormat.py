from Frame import Frame
import struct


class SFormat(Frame):
    def __init__(self, rsn = 0):
        super().__init__('S-format')
        self.rsn = rsn
    
    
    def serialize(self, rsn = 0):
        
        if rsn:
            self.rsn = rsn
        
        # here is specify format for S format
        third = (self.rsn & 0x7F) << 1
        fourth = (self.rsn >> 7) & 0xFF
        
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * (self.__header_length + 2)}", 
                                    Frame.__start_byte, # start byte
                                    self.__total_length,  # Total Length pouze hlavička
                                    1,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    third,   # 3. ridici pole
                                    fourth,  # 4. ridici pole
        )
        self.__structure = packed_header
        return self.__structure
    
     
    @property
    def rsn(self):
        return self.rsn
            
    
    @rsn.setter
    def rsn(self, rsn):
        self.rsn = rsn
        
    def increment_rsn(self):
        self.rsn += 1
        
        
    def __str__(self):
        return f"Typ: {self.__type_in_word}, Data in bytes: {self.serialize()}"
    
