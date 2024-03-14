from Frame import Frame
import struct
import acpi

class UFormat(Frame):
    def __init__(self, type = None):
        super().__init__('U-format')
        self.__type_int = type        
        self.__type_of_Uformat_Str = ''
        if type:
            self.type = type
        
    @property
    def type(self):
        return self.__type_int 
    
    @type.setter
    def type(self, type):
        self.__type_int = type
        if type == acpi.STARTDT_ACT:
            self.__type_of_Uformat_Str = 'STARTDT ACT'
            
        if type == acpi.STARTDT_CON:
            self.__type_of_Uformat_Str = 'STARTDT CON'
            
        if type == acpi.STOPDT_ACT:
            self.__type_of_Uformat_Str = 'STOPDT ACT'
            
        if type == acpi.STOPDT_CON:
            self.__type_of_Uformat_Str = 'STOPDT CON'
            
        if type == acpi.TESTFR_ACT:
            self.__type_of_Uformat_Str = 'TESTDT ACT'
            
        if type == acpi.TESTFR_CON:
            self.__type_of_Uformat_Str = 'TESTDT CON'
            
    @property
    def type_of_Uformat_Str(self):
        return self.__type_of_Uformat_Str
    
    @property
    def type_int(self):
        return self.__type_int
    
    def serialize(self, type = None):
        if type:
            self.type = type
        
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * (self._header_length + 2)}", 
                                    Frame._start_byte, # start byte
                                    self._total_length,  # Total Length pouze hlavička
                                    self.__type_int,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    0,   # 3. ridici pole
                                    0,  # 4. ridici pole
        )
        self.__structure = packed_header
        return packed_header
    
    
    def __str__(self):
        return f"Typ: {self._type_in_word}, U-format: {self.__type_of_Uformat_Str}"