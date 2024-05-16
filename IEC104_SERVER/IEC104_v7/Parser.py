# -*- coding: utf-8 -*-

import struct
from apci import APCI

from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat


class Parser:
    """
    This class is responsible for parsing the given APDU (Application Protocol Data Unit)
    and determining the format (I, S, U) of the APDU.
    """

    @classmethod
    def parser(cls, apdu, length: int) -> IFormat | SFormat | UFormat | None:
        """
        Parses the given APDU and returns the corresponding format object (IFormat, SFormat, UFormat).

        Parameters:
        apdu (bytes): The APDU to be parsed.
        length (int): The length of the APDU.

        Returns:
        IFormat | SFormat | UFormat | None: The corresponding format object or None if the format is unknown.
        """
        unpacked_apdu = struct.unpack(f"{'B' * length}", apdu)
        frame_format = Parser.what_format(unpacked_apdu)

        if frame_format == "I":
            # Parse I-Format
            ssn = (unpacked_apdu[1] << 7) + (unpacked_apdu[0] >> 1)
            rsn = (unpacked_apdu[3] << 7) + (unpacked_apdu[2] >> 1)
            data = struct.unpack(f"{'B' * length}", apdu)
            asdu_data = data[APCI.ACPI_HEADER_LENGTH:]
            new_instance = IFormat(bytes(asdu_data), ssn, rsn, direction='IN')
            return new_instance

        elif frame_format == "S":
            # Parse S-Format
            rsn = (unpacked_apdu[3] << 7) + (unpacked_apdu[2] >> 1)
            new_instance = SFormat(rsn, direction='IN')
            return new_instance

        elif frame_format == "U":
            # Parse U-Format
            first_byte = unpacked_apdu[0]
            new_instance = UFormat(direction='IN')

            # STARTDT ACT
            if first_byte == APCI.STARTDT_ACT:
                new_instance.type = APCI.STARTDT_ACT
                return new_instance

            # STOPDT ACT
            elif first_byte == APCI.STOPDT_ACT:
                new_instance.type = APCI.STOPDT_ACT
                return new_instance

            # TESTDT ACT
            elif first_byte == APCI.TESTFR_ACT:
                new_instance.type = APCI.TESTFR_ACT
                return new_instance

            elif first_byte == APCI.STARTDT_CON:
                new_instance.type = APCI.STARTDT_CON
                return new_instance

            # STOPDT CON
            elif first_byte == APCI.STOPDT_CON:
                new_instance.type = APCI.STOPDT_CON
                return new_instance

            # TESTDT CON
            elif first_byte == APCI.TESTFR_CON:
                new_instance.type = APCI.TESTFR_CON
                return new_instance

            else:
                # This should never happen
                raise Exception(f"Unexpected U-Format received: {first_byte}")

        else:
            # Unknown format
            raise Exception("Received unknown APDU format")

    @classmethod
    def what_format(cls, first_byte: tuple) -> str | None:
        """
        Determines the format (I, S, U) of the given APDU based on the first byte.

        Parameters:
        first_byte (tuple): The first byte of the APDU.

        Returns:
        str | None: The format of the APDU ("I", "S", "U") or None if the format is unknown.
        """
        first_byte = first_byte[0]

        if not (first_byte & 1):
            # I-Format
            return "I"
        elif (first_byte & 3) == 1:
            # S-Format
            return "S"
        elif (first_byte & 3) == 3:
            # U-Format
            return "U"
        else:
            # Unknown format
            return None
