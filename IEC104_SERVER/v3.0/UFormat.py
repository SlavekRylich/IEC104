from Frame import Frame
import struct
import acpi

class UFormat(Frame):
    def __init__(self, type = None):
        super().__init__('U-format')
        self._type_int = type        
        self._type_of_Uformat_Str = ''
        if type:
            self._type(type)
        
    @property
    def _type(self):
        return self._type_int 
    
    @_type.setter
    def _type(self, type):
        self._type_int = type
        if type == acpi.STARTDT_ACT:
            self._type_of_Uformat_Str = 'STARTDT ACT'
            
        if type == acpi.STARTDT_CON:
            self._type_of_Uformat_Str = 'STARTDT CON'
            
        if type == acpi.STOPDT_ACT:
            self._type_of_Uformat_Str = 'STOPDT ACT'
            
        if type == acpi.STOPDT_CON:
            self._type_of_Uformat_Str = 'STOPDT CON'
            
        if type == acpi.TESTFR_ACT:
            self._type_of_Uformat_Str = 'TESTDT ACT'
            
        if type == acpi.TESTFR_CON:
            self._type_of_Uformat_Str = 'TESTDT CON'
            
    @property
    def _type_of_Uformat_Str(self):
        return self._type_of_Uformat_Str
    
    @property
    def _type_int(self):
        return self._type_int
    
    def serialize(self, type = None):
        if type:
            self._type(type)
        
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * (self.__header_length + 2)}", 
                                    Frame.__start_byte, # start byte
                                    self.__total_length,  # Total Length pouze hlavička
                                    self._type_int,   # 1. ridici pole
                                    0,  # 2. ridici pole
                                    0,   # 3. ridici pole
                                    0,  # 4. ridici pole
        )
        self.__structure = packed_header
        return packed_header
    
    
    def __str__(self):
        return f"Typ: {self.__type_in_word}, U-format: {self._type_of_Uformat_Str}, Data in bytes: {self.serialize()}"