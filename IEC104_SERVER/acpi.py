# -*- coding: utf-8 -*-
import struct

# define 
ACPI_HEADER_LENGTH = 4
START_BYTE = 0x68

TESTFR_ACT = 0x43
TESTFR_CON = 0x83

STOPDT_ACT = 0x13
STOPDT_CON = 0x23

STARTDT_ACT = 0x07
STARTDT_CON = 0x0b

T0 = 30     # t0 = 30s  - Time delay for init session
T1 = 15     # t1 = 15s  - Time delay for transmission or test APDU
T2 = 10     # t2 = 10s  - Time delay for confirmation if that messages do not contain data t2 < t1
T3 = 20     # t3 = 20s  - Time delay for test transmission frames in case of long idle states


def i_frame(ssn, rsn):
    return struct.pack('<1BHH', 0x64, ssn << 1, rsn << 1)


def s_frame(rsn):
    return struct.pack('<3BH', 0x64, 0x01, 0x00, rsn << 1)


def parse_i_frame(data):
    ssn, rsn = struct.unpack('<2H', data)
    return ssn >> 1, rsn >> 1


def parse_s_frame(data):
    rsn = struct.unpack_from('<2H', data)[1]
    return rsn >> 1
