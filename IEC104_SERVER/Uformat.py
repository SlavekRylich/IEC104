from Frame import Frame
import struct
import acpi

class UFormat(Frame):
    def __init__(self, type = None):
        super().__init__('U-format')
        self.type_int = type        
        self.type_of_Uformat_Str = ''
        if type:
            self.set_type(type)
        
    #property
    def get_type(self):
        return self.type_int 
    
    def set_type(self, type):
        self.type_int = type
        if type == acpi.STARTDT_ACT:
            self.type_of_Uformat_Str = 'STARTDT ACT'
            
        if type == acpi.STARTDT_CON:
            self.type_of_Uformat_Str = 'STARTDT CON'
            
        if type == acpi.STOPDT_ACT:
            self.type_of_Uformat_Str = 'STOPDT ACT'
            
        if type == acpi.STOPDT_CON:
            self.type_of_Uformat_Str = 'STOPDT CON'
            
        if type == acpi.TESTFR_ACT:
            self.type_of_Uformat_Str = 'TESTDT ACT'
            
        if type == acpi.TESTFR_CON:
            self.type_of_Uformat_Str = 'TESTDT CON'
            
        
    def get_type_of_Uformat_Str(self):
        return self.type_of_Uformat_Str
    
    def get_type_int(self):
        return self.type_int
    
    # serializace dat 
    def serialize(self, type = None):
        if type:
            self.set_type(type)
        
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * (self.header_length + 2)}", 
                                    Frame.start_byte, # start byte
                                    self.total_length,  # Total Length pouze hlavička
                                    self.type_int,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    0,   # 3. ridici pole
                                    0,  # 4. ridici pole
        )
        self.structure = packed_header
        return packed_header
    
    
    def __str__(self):
        return f"Typ: {self.type_in_word}, U-format: {self.type_of_Uformat_Str}, Data in bytes: {self.serialize()}"