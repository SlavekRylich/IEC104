import math
import struct

from ASDU import ASDU, MMeNc1

if __name__ == "__main__":
    # data = b'\x01\x06\x03\x01\x20\x02\x00\x00\x14'
    data = b'\x64\x01\x06\x03\x01\x00\x00\x00\x00\x14'
    # priklady z prace pana Matouska
    # \x68\x0E\x4E\x14\x7C\x00 - APCI
    data1 = b'\x65\x01\x0A\x00\x0C\x00\x00\x00\x00\x05'
    # \x68\x34\x5A\x14\x7C\x00 - APCI
    data2 = (b'\x0B\x07\x03\x00\x0C\x00\x10\x30\x00\xBE\x09\x00\x11\x30'
             b'\x00\x90\x09\x00\x0E\x30\x00\x75\x00\x00\x28\x30\x00\x25\x09\x00\x29\x30\x00\x75'
             b'\x00\x00\x0F\x30\x00\x0F\x0A\x00\x2E\x30\x00\xAE\x05\x00')

    dotaz_cteni_102 = b'\x66\x01\x05\x00\x0C\x00\x10\x30\x00'
    # hodnota ve floating point
    merena_teplota_11 = b'\x0D\x81\x05\x00\x0C\x00\x10\x30\x00\x42\xF6\x00\x11\x30'
    # aktivace
    povel_aktivace_45 = b'\x2D\x01\x06\x00\x0C\x00\x10\x30\x00\x01'
    # deaktivace
    povel_deaktivace_45 = b'\x2D\x01\x06\x00\x0C\x00\x10\x30\x00\x01'

    povel_potvrzeni_aktivace_45 = b'\x2D\x01\x07\x00\x0C\x00\x10\x30\x00\x00'
    povel_potvrzeni_deaktivace_45 = b'\x2D\x01\x08\x00\x0C\x00\x10\x30\x00\x00'

    o_data = ASDU(merena_teplota_11)
    # new_data = MMeNc1(75.5)
    print(o_data)

    #
    # def float_to_binary_single_precision(float_number):
    #     """
    #     Převod desetinného čísla s plovoucí desetinnou čárkou do binární podoby v single precision (formát IEEE 754).
    #
    #     Args:
    #         float_number: Desetinné číslo s plovoucí desetinnou čárkou.
    #
    #     Returns:
    #         Řetězec s binární reprezentací čísla rozdělený na bity.
    #     """
    #
    #     # Zkontrolujte, zda je číslo v rozsahu single precision
    #     if not (-3.4028235e38 <= float_number <= 3.4028235e38):
    #         raise ValueError(f"Číslo {float_number} je mimo rozsah single precision.")
    #
    #     # Normalizace
    #     sign = 1 if float_number < 0 else 0
    #     exponent, mantissa = math.frexp(abs(float_number))
    #
    #     # Vypočítání exponentu v single precision
    #     exponent_bias = 127
    #     exponent_single_precision = int(exponent + exponent_bias)
    #
    #     # Vypočítání mantisy v single precision
    #     mantissa_single_precision = mantissa * 2 ** 23
    #
    #
    #     # Sestavení binární reprezentace
    #     binary_representation = (f"{sign:b}{bin(exponent_single_precision)[2:].zfill(8)}"
    #                              f"{bin(int(mantissa_single_precision))[2:].zfill(23)}")
    #
    #     # Rozdělení na bity
    #     bit_groups = [binary_representation[i: i + 8] for i in range(0, len(binary_representation), 8)]
    #
    #     return " ".join(bit_groups)
    #     # return binary_representation
    #
    #
    # # Příklad použití
    # float_number = 1.01733e-28
    # binary_representation = float_to_binary_single_precision(float_number)
    # print(f"Binární reprezentace (single precision): {binary_representation}")
    # # print(struct.unpack("BBBB", hex(binary_representation)))

    import struct


    def float_to_bytes_single_precision(float_number):
        if not (-3.4028235e38 <= float_number <= 3.4028235e38):
            raise ValueError(f"Číslo {float_number} je mimo rozsah single precision.")

        # Normalizace
        sign = 1 if float_number < 0 else 0
        exponent, mantissa = math.frexp(abs(float_number))

        # Vypočítání exponentu v single precision
        exponent_bias = 127
        exponent_single_precision = int(exponent + exponent_bias)

        # Vypočítání mantisy v single precision
        mantissa_single_precision = mantissa * 2 ** 23

        # Sestavení binární reprezentace
        binary_representation = f"{sign:b} {bin(exponent_single_precision)[2:].zfill(8)} {bin(int(mantissa_single_precision))[2:].zfill(23)}"

        # Převod binární reprezentace do bytes
        bytes_representation = struct.pack("<f", float_number)

        return bytes_representation


    # Příklad použití
    float_number = 1.01733e-28
    bytes_representation = float_to_bytes_single_precision(float_number)
    print(f"Binární reprezentace (bytes): {bytes_representation.hex()}")
    print(bytes_representation)

    import struct


    def bytes_to_float_single_precision(bytes_representation):
        """
        Převod bytes reprezentujících binární reprezentaci čísla v single precision (formát IEEE 754) na desetinné číslo s plovoucí desetinnou čárkou.

        Args:
            bytes_representation: Bytes reprezentující binární reprezentaci čísla.

        Returns:
            Desetinné číslo s plovoucí desetinnou čárkou.
        """

        # Převeď bytes na bitový řetězec a ujisti se, že má délku násobku 8
        binary_representation = bin(int.from_bytes(bytes_representation, byteorder='big'))[2:].zfill(
            len(bytes_representation) * 8)

        # Rozdělení bitového řetězce na skupiny po 8 bitů
        sign_bits = binary_representation[0:8]
        exponent_bits = binary_representation[8:16]
        mantissa_bits = binary_representation[16:]

        # Vypočtení hodnot
        sign = 1 if sign_bits[0] == '1' else -1
        exponent_single_precision = int(exponent_bits, 2) - 127
        mantissa_single_precision = int(mantissa_bits, 2) / 2 ** 23

        # Sestavení desetinného čísla
        float_number = sign * mantissa_single_precision * 2 ** exponent_single_precision

        return float_number


    # Příklad použití
    # bytesa = b'\x11\x00\xf6\x42'
    bytesa = b'\x42\xf6\x00\x11'
    bytes_representation = struct.unpack("BBBB", bytesa)
    print(f"here {bytes_representation}")
    # bytes_representation = struct.pack("<f", -2.125)
    float_number = bytes_to_float_single_precision(bytes_representation)
    print(f"Desetinné číslo: {float_number}")


    def binary(num):
        # Struct can provide us with the float packed into bytes. The '!' ensures that
        # it's in network byte order (big-endian) and the 'f' says that it should be
        # packed as a float. Alternatively, for double-precision, you could use 'd'.
        packed = struct.pack('!f', num)
        print('Packed: %s' % repr(packed))

        # For each character in the returned string, we'll turn it into its corresponding
        # integer code point
        #
        # [62, 163, 215, 10] = [ord(c) for c in '>\xa3\xd7\n']
        integers = [ord(chr(c)) for c in packed]
        print('Integers: %s' % integers)

        # For each integer, we'll convert it to its binary representation.
        binaries = [bin(i) for i in integers]
        print('Binaries: %s' % binaries)

        # Now strip off the '0b' from each of these
        stripped_binaries = [s.replace('0b', '') for s in binaries]
        print('Stripped: %s' % stripped_binaries)

        # Pad each byte's binary representation's with 0's to make sure it has all 8 bits:
        #
        # ['00111110', '10100011', '11010111', '00001010']
        padded = [s.rjust(8, '0') for s in stripped_binaries]
        print('Padded: %s' % padded)

        # At this point, we have each of the bytes for the network byte ordered float
        # in an array as binary strings. Now we just concatenate them to get the total
        # representation of the float:
        return ''.join(padded)


    number: float = 1.01733e-28
    print(number)
    print({binary(number)})
    binary(number)
