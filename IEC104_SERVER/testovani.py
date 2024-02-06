

from ctypes import c_uint8
import math




data = b'abcdefasdf afg fghfgh'  # Nahraďte svými daty
byte_length = len(data)
rounded_byte_length = math.ceil(byte_length / 8)   # Zaokrouhlení na násobek 8 bajtů

print(f"Délka dat: {byte_length} bitů")
print(f"Zaokrouhlená délka na násobek 8 bitů: {rounded_byte_length} B")



