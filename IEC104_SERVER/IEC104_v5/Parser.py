import struct
import acpi

from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat


class Parser:
    @classmethod
    def parser(cls, apdu, length: int) -> IFormat | SFormat | UFormat | None:
        unpacked_apdu = struct.unpack(f"{'B' * (length)}", apdu)
        frame_format = Parser.what_format(unpacked_apdu)

        if frame_format == "I":
            ssn = (unpacked_apdu[1] << 7) + (unpacked_apdu[0] >> 1)
            rsn = (unpacked_apdu[3] << 7) + (unpacked_apdu[2] >> 1)
            data = struct.unpack(f"{'B' * (length)}", apdu)
            asdu_data = data[acpi.ACPI_HEADER_LENGTH:]
            new_instance = IFormat(bytes(asdu_data), ssn, rsn, direction='IN')
            return new_instance

        elif frame_format == "S":
            rsn = (unpacked_apdu[3] << 7) + (unpacked_apdu[2] >> 1)
            new_instance = SFormat(rsn, direction='IN')
            return new_instance

        elif frame_format == "U":
            first_byte = unpacked_apdu[0]
            new_instance = UFormat(direction='IN')

            # STARTDT ACT
            if first_byte == acpi.STARTDT_ACT:
                new_instance.type = acpi.STARTDT_ACT
                return new_instance

            # STOPDT ACT
            elif first_byte == acpi.STOPDT_ACT:
                new_instance.type = acpi.STOPDT_ACT
                return new_instance

            # TESTDT ACT
            elif first_byte == acpi.TESTFR_ACT:
                new_instance.type = acpi.TESTFR_ACT
                return new_instance

            elif first_byte == acpi.STARTDT_CON:
                new_instance.type = acpi.STARTDT_CON
                return new_instance

            # STOPDT ACT
            elif first_byte == acpi.STOPDT_CON:
                new_instance.type = acpi.STOPDT_CON
                return new_instance

            # TESTDT ACT
            elif first_byte == acpi.TESTFR_CON:
                new_instance.type = acpi.TESTFR_CON
                return new_instance

            else:
                # nemělo by nikdy nastat
                raise Exception(f"Nemelo by nastat")

        else:
            raise Exception("Přijat neznámí formát")

    @classmethod
    def what_format(cls, first_byte: tuple) -> str | None:
        first_byte = first_byte[0]

        if not (first_byte & 1):
            # print(f"I format {first_byte & 0xFF}")
            return "I"
        elif (first_byte & 3) == 1:
            # print(f"S format {first_byte & 0xFF}")
            return "S"
        elif (first_byte & 3) == 3:
            # print(f"U format {first_byte & 0xFF}")
            return "U"
        else:
            # print("Nejaky jiný format")
            return None
