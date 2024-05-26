# -*- coding: utf-8 -*-
import logging
import struct

LOG = logging.getLogger()


def bytes_to_float(value: bytes):
    nexp = 8
    len_frac = 23

    first_byte = value[3]
    second_byte = value[2]
    third_byte = value[1]
    fourth_byte = value[0]

    sign = (first_byte & 128) >> 7
    exp = ((first_byte & 127) << 1) + (second_byte >> 7)
    bias = 2 ** (nexp - 1) - 1
    exponent = exp - bias
    fract = (((second_byte & 127) + 128) << 16) + (third_byte << 8) + fourth_byte

    mantisa = fract / 2 ** (len_frac - exponent)
    if sign:
        result = (-1) * mantisa
    else:
        result = mantisa
    return result


class ASDU:
    def __init__(self, data=None,
                 type_id=None,
                 sq=None,
                 sq_count=None,
                 test_bit=None,
                 p_n_bit=None,
                 cot=None,
                 org_OA=None,
                 addr_COA=None,
                 ):

        self.objs: list = []
        self.obj_elements = []
        if data is not None:
            self.data = data
            format = f"{'B' * (len(data))}"
            unpack_data = struct.unpack(format, data)
            self.type_id = unpack_data[0]  # first byte

            #   1XXX_XXXX
            #  *1000_0000
            self.sq = (unpack_data[1] & 128) >> 7  # Single or Sequence

            #   X000_0000
            #  *0111_1111
            self.sq_count = unpack_data[1] & 127

            #   T | P/N |  C5  |  C4  |  C3  |  C2  |  C1  |  C0  |
            self.test_bit = bool(unpack_data[2] & 128)
            self.p_n_bit = bool(unpack_data[2] & 64)
            self.cot = unpack_data[2] & 63

            self.org_OA = unpack_data[3]
            self.addr_COA = (unpack_data[5] << 8) + unpack_data[4]

            # in bytes
            self.length = 6

            # zbytek dat
            self.asdu_tuple = unpack_data[6:]

            # LOG.debug("Type: {}, COT: {}, ASDU: {}".format(self.type_id, self.cot, self.addr))

            # has more info objects
            if not self.sq:
                for i in range(self.sq_count):
                    obj = InfoObjMeta.types[self.type_id](self.asdu_tuple)
                    # obj = InfoObjMeta.types[self.type_id](data)
                    self.objs.append(obj)
                    if obj.length:
                        self.length += obj.length

            # has one info object
            else:
                for i in range(self.sq_count):
                    obj = InfoObjMeta.types[self.type_id](self.asdu_tuple)
                    # obj = InfoObjMeta.types[self.type_id](data)
                    self.objs.append(obj)
                    if obj.length:
                        self.length += obj.length
                pass

        else:
            self.type_id = type_id
            self.sq = sq
            self.sq_count = sq_count
            self.test_bit = test_bit
            self.p_n_bit = p_n_bit
            self.cot = cot
            self.org_OA = org_OA
            self.addr_COA = addr_COA
            self.length = 6

    def add_obj(self, obj):
        self.objs.append(obj)
        self.length += len(obj.serial_obj)
        self.length += len(obj.serial_data)

    def add_obj_element(self, obj_elements):
        self.obj_elements.append(obj_elements)

    def serialize(self):
        length = 6  #self.length
        # for obj in self.objs:
        #     length += len(obj.length)
        a = self.sq << 7

        form = f"{'B' * length}"
        data = struct.pack(form, self.type_id
                           , (self.sq << 7) + self.sq_count
                           , (self.test_bit << 7) + (self.p_n_bit << 6) + self.cot
                           , self.org_OA
                           , self.addr_COA & 255
                           , self.addr_COA >> 8
                           )
        for obj in self.objs:
            data += obj.serial_obj + obj.serial_data
        return data


class QDS(object):
    def __init__(self, data):
        self.overflow = bool(data & 0x01)
        self.blocked = bool(data & 0x10)
        self.substituted = bool(data & 0x20)
        self.not_topical = bool(data & 0x40)
        self.invalid = bool(data & 0x80)
        self.in_number = data


class SCO(object):
    def __init__(self, data):
        # super(SCO, self).__init__(unpacked_data)
        self.qoc = QOC(data)
        self.on_off = bool(data & 1)
        self.in_number = data


class QOC(object):
    def __init__(self, data):
        self.execute = bool(data & 128)
        self.pulse_id = (data & 124) >> 2


class InfoObjMeta(type):
    types = {}

    def __new__(mcs, name, bases, dct):
        re = type.__new__(mcs, name, bases, dct)
        if 'type_id' in dct:
            InfoObjMeta.types[dct['type_id']] = re
        return re


class InfoObj(metaclass=InfoObjMeta):

    def __init__(self, unpacked_data=None, ioa=None, special_uses=None):
        self.special_uses = 0
        if unpacked_data is not None:
            self.ioa = (unpacked_data[1] << 8) + unpacked_data[0]
            self.special_uses = (unpacked_data[2] << 16) + (unpacked_data[1] << 8) + unpacked_data[0]

        if ioa:
            self.ioa = ioa
        if special_uses:
            self.special_uses = special_uses
        self.length = 3
        self.serial_obj = self.serialize_obj()

    def serialize_obj(self):
        return struct.pack(f"{'B' * self.length}", self.ioa & 255
                           , self.ioa >> 8
                           , self.special_uses >> 16
                           )


class SIQ(InfoObj):
    def __init__(self, unpacked_data):
        if isinstance(unpacked_data, tuple):
            super(SIQ, self).__init__(unpacked_data)
            self.iv = unpacked_data[0] & 128
            self.nt = unpacked_data[0] & 64
            self.sb = unpacked_data[0] & 32
            self.bl = unpacked_data[0] & 16
            # ...._XXX. - reserve
            self.spi = unpacked_data[0] & 1

        elif isinstance(unpacked_data, int):
            super(SIQ, self).__init__((unpacked_data,))
            self.iv = unpacked_data & 128
            self.nt = unpacked_data & 64
            self.sb = unpacked_data & 32
            self.bl = unpacked_data & 16
            # ...._XXX. - reserve
            self.spi = unpacked_data & 1


class DIQ(InfoObj):
    def __init__(self, unpacked_data):
        super(DIQ, self).__init__(unpacked_data)
        self.iv = unpacked_data[0] & 128
        self.nt = unpacked_data[0] & 64
        self.sb = unpacked_data[0] & 32
        self.bl = unpacked_data[0] & 16
        # unpacked_data.read('int:2')  # reserve
        # ...._XX.. - reserve
        self.dpi = unpacked_data[0] & 3
        # self.dpi = unpacked_data.read('uint:2')


class MSpNa1(SIQ):
    type_id = 1
    name = 'M_SP_NA_1'
    description = 'Single-point information without time tag'

    def __init__(self, unpacked_data):
        super(MSpNa1, self).__init__(unpacked_data)
        LOG.debug('Obj: M_SP_NA_1, Value: {}'.format(self.spi))


class MSpTa1(InfoObj):
    type_id = 2
    name = 'M_SP_TA_1'
    description = 'Single-point information with time tag'

    def __init__(self, unpacked_data):
        super(MSpTa1, self).__init__(unpacked_data)


class MDpNa1(DIQ):
    type_id = 3
    name = 'M_DP_NA_1'
    description = 'Double-point information without time tag'

    def __init__(self, unpacked_data):
        super(MDpNa1, self).__init__(unpacked_data)
        LOG.debug('Obj: M_DP_NA_1, Value: {}'.format(self.dpi))


class MDpTa1(InfoObj):
    type_id = 4
    name = 'M_DP_TA_1'
    description = 'Double-point information with time tag'


class MStNa1(InfoObj):
    type_id = 5
    name = 'M_ST_NA_1'
    description = 'Step position information'


class MStTa1(InfoObj):
    type_id = 6
    name = 'M_ST_TA_1'
    description = 'Step position information with time tag'


class MBoNa1(InfoObj):
    type_id = 7
    name = 'M_BO_NA_1'
    description = 'Bitstring of 32 bit'


class MBoTa1(InfoObj):
    type_id = 8
    name = 'M_BO_TA_1'
    description = 'Bitstring of 32 bit with time tag'


class MMeNa1(InfoObj):
    type_id = 9
    name = 'M_ME_NA_1'
    description = 'Measured value, normalized value'

    def __init__(self, unpacked_data):
        super(MMeNa1, self).__init__(unpacked_data)
        self.nva = unpacked_data[0]
        self.nva = (unpacked_data[2] << 8) + unpacked_data[1]
        # self.nva = unpacked_data.read('int:8')
        # self.nva = unpacked_data.read('int:16')
        LOG.debug('Obj: M_ME_NA_1, Value: {}'.format(self.nva))


class MMeTa1(InfoObj):
    type_id = 10
    name = 'M_ME_TA_1'
    description = 'Measured value, normalized value with time tag'


class MMeNb1(InfoObj):
    type_id = 11
    name = 'M_ME_NB_1'
    description = 'Measured value, scaled value'


class MMeTb1(InfoObj):
    type_id = 12
    name = 'M_ME_TB_1'
    description = 'Measured value, scaled value with time tag'


class MMeNc1(InfoObj):
    type_id = 13
    name = 'M_ME_NC_1'
    description = 'Measured value, short floating point number'
    length = 5

    def __init__(self, unpacked_data=None, ioa=None, value=None, qds=None):
        super(MMeNc1, self).__init__(unpacked_data, ioa)
        self.unpack_value = 0
        self.qds = qds
        if unpacked_data:
            self.value = bytes_to_float(unpacked_data[3:7])
            self.qds = QDS(unpacked_data[7])

        if value is not None:
            self.value = value
            self.value_bytes = pack = struct.pack("<f", value)
            formate = f"{'B' * (len(self.value_bytes))}"
            self.unpack_value = struct.unpack(formate, self.value_bytes)
        if qds is not None:
            self.qds = QDS(qds)

        self.serial_data = self.serialize_MMeNc1()

    def serialize_MMeNc1(self):
        return struct.pack(f"{'B' * MMeNc1.length}"
                           , self.unpack_value[0]
                           , self.unpack_value[1]
                           , self.unpack_value[2]
                           , self.unpack_value[3]
                           , self.qds.in_number
                           )


class MMeTc1(InfoObj):
    type_id = 14
    name = 'M_ME_TC_1'
    description = 'Measured value, short floating point number with time tag'


class MItNa1(InfoObj):
    type_id = 15
    name = 'M_IT_NA_1'
    description = 'Integrated totals'


class MItTa1(InfoObj):
    type_id = 16
    name = 'M_IT_TA_1'
    description = 'Integrated totals with time tag'


class MEpTa1(InfoObj):
    type_id = 17
    name = 'M_EP_TA_1'
    description = 'Event of protection equipment with time tag'


class MEpTb1(InfoObj):
    type_id = 18
    name = 'M_EP_TB_1'
    description = 'Packed start events of protection equipment with time tag'


class MEpTc1(InfoObj):
    type_id = 19
    name = 'M_EP_TC_1'
    description = 'Packed output circuit information of protection equipment with time tag'


class MPsNa1(InfoObj):
    type_id = 20
    name = 'M_PS_NA_1'
    description = 'Packed single-point information with status change detection'


class MMeNd1(InfoObj):
    type_id = 21
    name = 'M_ME_ND_1'
    description = 'Measured value, normalized value without quality descriptor'


class MSpTb1(InfoObj):
    type_id = 30
    name = 'M_SP_TB_1'
    description = 'Single-point information with time tag CP56Time2a'


class MDpTb1(InfoObj):
    type_id = 31
    name = 'M_DP_TB_1'
    description = 'Double-point information with time tag CP56Time2a'


class MStTb1(InfoObj):
    type_id = 32
    name = 'M_ST_TB_1'
    description = 'Step position information with time tag CP56Time2a'


class MBoTb1(InfoObj):
    type_id = 33
    name = 'M_BO_TB_1'
    description = 'Bitstring of 32 bits with time tag CP56Time2a'


class MMeTd1(InfoObj):
    type_id = 34
    name = 'M_ME_TD_1'
    description = 'Measured value, normalized value with time tag CP56Time2a'


class MMeTe1(InfoObj):
    type_id = 35
    name = 'M_ME_TE_1'
    description = 'Measured value, scaled value with time tag CP56Time2a'


class MMeTf1(InfoObj):
    type_id = 36
    name = 'M_ME_TF_1'
    description = 'Measured value, short floating point number with time tag CP56Time2a'


class MItTb1(InfoObj):
    type_id = 37
    name = 'M_IT_TB_1'
    description = 'Integrated totals with time tag CP56Time2a'


class MEpTd1(InfoObj):
    type_id = 38
    name = 'M_EP_TD_1'
    description = 'Event of protection equipment with time tag CP56Time2a'


class MEpTe1(InfoObj):
    type_id = 39
    name = 'M_EP_TE_1'
    description = 'Packed start events of protection equipment with time tag CP56Time2a'


class MEpTf1(InfoObj):
    type_id = 40
    name = 'M_EP_TF_1'
    description = 'Packed output circuit information of protection equipment with time tag CP56Time2a'


class CScNa1(InfoObj):
    type_id = 45
    name = 'C_SC_NA_1'
    description = 'Single command'
    length = 1

    def __init__(self, unpacked_data=None, ioa=None, sco=None):
        super(CScNa1, self).__init__(unpacked_data, ioa=ioa)

        if unpacked_data is not None:
            self.sco = SCO(unpacked_data[3])
        if sco is not None:
            self.sco = SCO(sco)
        self.serial_data = self.serialize_CScNa1()

    def serialize_CScNa1(self):
        return struct.pack(f"{'B' * CScNa1.length}"
                           , self.sco.in_number
                           )


class CDcNa1(InfoObj):
    type_id = 46
    name = 'C_DC_NA_1'
    description = 'Double command'


class CRcNa1(InfoObj):
    type_id = 47
    name = 'C_RC_NA_1'
    description = 'Regulating step command'


class CSeNa1(InfoObj):
    type_id = 48
    name = 'C_SE_NA_1'
    description = 'Set-point command, normalized value'


class CSeNb1(InfoObj):
    type_id = 49
    name = 'C_SE_NB_1'
    description = 'Set-point command, scaled value'


class CSeNc1(InfoObj):
    type_id = 50
    name = 'C_SE_NC_1'
    description = 'Set-point command, short floating point number'


class CBoNa1(InfoObj):
    type_id = 51
    name = 'C_BO_NA_1'
    description = 'Bitstring of 32 bit'


class MEiNa1(InfoObj):
    type_id = 70
    name = 'M_EI_NA_1'
    description = 'End of initialization'


class CIcNa1(InfoObj):
    type_id = 100
    name = 'C_IC_NA_1'
    description = 'Interrogation command'


class CCiNa1(InfoObj):
    type_id = 101
    name = 'C_CI_NA_1'
    description = 'Counter interrogation command'


class CRdNa1(InfoObj):
    type_id = 102
    name = 'C_RD_NA_1'
    description = 'Read command'
    length = 1


class CCsNa1(InfoObj):
    type_id = 103
    name = 'C_CS_NA_1'
    description = 'Clock synchronization command'


class CTsNa1(InfoObj):
    type_id = 104
    name = 'C_TS_NA_1'
    description = 'Test command'


class CRpNa1(InfoObj):
    type_id = 105
    name = 'C_RP_NA_1'
    description = 'Reset process command'


class CCdNa1(InfoObj):
    type_id = 106
    name = 'C_CD_NA_1'
    description = 'Delay acquisition command'


class PMeNa1(InfoObj):
    type_id = 110
    name = 'P_ME_NA_1'
    description = 'Parameter of measured values, normalized value'


class PMeNb1(InfoObj):
    type_id = 111
    name = 'P_ME_NB_1'
    description = 'Parameter of measured values, scaled value'


class PMeNc1(InfoObj):
    type_id = 112
    name = 'P_ME_NC_1'
    description = 'Parameter of measured values, short floating point number'


class PAcNa1(InfoObj):
    type_id = 113
    name = 'P_AC_NA_1'
    description = 'Parameter activation'


class FFrNa1(InfoObj):
    type_id = 120
    name = 'F_FR_NA_1'
    description = 'File ready'


class FSrNa1(InfoObj):
    type_id = 121
    name = 'F_SR_NA_1'
    description = 'Section ready'


class FScNa1(InfoObj):
    type_id = 122
    name = 'F_SC_NA_1'
    description = 'Call directory, select file, call file, call section'


class FLsNa1(InfoObj):
    type_id = 123
    name = 'F_LS_NA_1'
    description = 'Last section, last segment'


class FAdNa1(InfoObj):
    type_id = 124
    name = 'F_AF_NA_1'
    description = 'ACK file, ACK section'


class FSgNa1(InfoObj):
    type_id = 125
    name = 'F_SG_NA_1'
    description = 'Segment'


class FDrTa1(InfoObj):
    type_id = 126
    name = 'F_DR_TA_1'
    description = 'Directory'
