# -*- coding: utf-8 -*-


class ACPI:
    # define
    ACPI_HEADER_LENGTH: int = 4
    START_BYTE: int = 0x68

    TESTFR_ACT: int = 0x43   # 67
    TESTFR_CON: int = 0x83   # 131

    STOPDT_ACT: int = 0x13   # 19
    STOPDT_CON: int = 0x23   # 35

    STARTDT_ACT: int = 0x07  # 07
    STARTDT_CON: int = 0x0b  # 11
