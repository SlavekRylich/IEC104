import Frame
import struct


class SFormat(Frame):
    def __init__(self):
        super().__init__(self)
        self.rsn = 0
        

    @property
    def structure(self):
        # here is specify format for S format 
        total_length = len(packed_header)
            # Doplnění délky do hlavičky
        packed_header = struct.pack(f"{'B' * acpi.ACPI_HEADER_LENGTH}", 
                                    self.start_byte, # start byte
                                    total_length,  # Total Length pouze hlavička
                                    first,   # 1. ridici pole
                                    second,  # 2. ridici pole
                                    third,   # 3. ridici pole
                                    fourth,  # 4. ridici pole
        )
        return self.structure
    
    @structure.setter
    def structure(self, value):
        self.structure = value