import math
import struct


def temperature_to_single_precision_bytes(number):
    """
    Převod zadané měřené teploty (°C) do single precision reprezentace a tisk v bytech.

    Args:
        number: Měřená teplota (°C) v desetinné čárce.

    Returns:
        Nic, ale vytiskne binární reprezentaci v bytech.
    """

    # Normalizace
    offset = 273.15  # Posun pro převod na Kelviny
    num = number + offset
    if number >= 0:
        sign = 1
    else:
        sign = 0

    # Vypočítání exponentu v single precision
    exponent_bias = 127
    exponent_single_precision = int(math.log2(num) + exponent_bias)

    # Vypočítání mantisy v single precision
    mantissa_single_precision = (num * 2 ** 23) - 2 ** 23

    # Sestavení binární reprezentace
    binary_representation = (f"{1:b} {bin(exponent_single_precision)[2:].zfill(8)}"
                             f" {bin(int(mantissa_single_precision))[2:].zfill(23)}")

    # Převod binární reprezentace do bytes
    bytes_representation = struct.pack("<f", number)

    # Tisk binární reprezentace v bytech
    print(f"Binární reprezentace (bytes): {bytes_representation}")



def bytes_to_temperature_single_precision(bytes_representation):
    nexp = 8
    len_frac = 23

    first_byte = bytes_representation[3]
    second_byte = bytes_representation[2]
    third_byte = bytes_representation[1]
    fourth_byte = bytes_representation[0]

    sign = (first_byte & 128) >> 7
    exp = ((first_byte & 127) << 1) + (second_byte >> 7)
    bias = 2**(nexp - 1) - 1
    exponent = exp - bias
    fract = (((second_byte & 127) + 128) << 16) + (third_byte << 8) + fourth_byte

    mantisa = fract / 2**(len_frac-exponent)
    if sign:
        result = (-1) * mantisa
    else:
        result = mantisa
    return result


# Příklad použití
temperature = 1.01004e-28
print(temperature)
pack = struct.pack("<f", temperature)
print(pack)
unpack = struct.unpack("<f", pack)
print(unpack[0])
temperature_to_single_precision_bytes(temperature)

# Příklad použití
bytes_representation = struct.pack("<f", -75.3)
# bytes_representation = b'\xcd\xcc\x96\xc2'
# \xBE\x09\x00\x11
# bytes_representation = b'\x9a\x99\x96\xc2'
bytes_representation = b'\x9a\x99\x96\xc2'
temperature = bytes_to_temperature_single_precision(bytes_representation)
print(f"Měřená teplota (°C): {temperature}")
