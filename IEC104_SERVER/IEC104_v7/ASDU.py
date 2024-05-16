# -*- coding: utf-8 -*-
import logging
import binascii
import struct

LOG = logging.getLogger()


class ASDU:
    def __init__(self, data):
        print("hex: ", binascii.hexlify(data).decode)

        format = f"{'B' * (len(data))}"
        print(len(data))
        unpack_data = struct.unpack(format, data)
        print(unpack_data)
        self.type_id = unpack_data[0]  # first byte
        # self.type_id = data.read('uint:8')

        #   1XXX_XXXX
        #  *1000_0000
        sq = unpack_data[1] & 128  # Single or Sequence

        # sq = data.read('bool')  # Single or Sequence
        #   X000_0000
        #  *0111_1111
        sq_count = unpack_data[1] & 127
        # sq_count = data.read('uint:7')

        #   T | P/N |  C5  |  C4  |  C3  |  C2  |  C1  |  C0  |
        test_bit = unpack_data[2] & 128
        p_n_bit = unpack_data[2] & 64
        self.cot = unpack_data[2] & 63
        # self.cot = data.read('uint:8')

        self.org = unpack_data[3]
        self.addr_COA = (unpack_data[5] << 8) + unpack_data[4]

        # zbytek dat
        self.asdu = unpack_data[6:]
        #
        # self.IOA = (unpack_data[8] << 16) + (unpack_data[7] << 8) + unpack_data[6]
        # self.QOI = unpack_data[9]

        print(f"TypeId: {self.type_id}\n"
              f"SQ: {bool(sq)}\n"
              f"NumIx: {sq_count}\n"
              f"CauseTx: {self.cot}\n"
              f"Negative: {bool(p_n_bit)}\n"
              f"Test: {bool(test_bit)}\n"
              f"OA: {self.org}\n"
              f"Addr: {self.addr_COA}\n"
              )
        # LOG.debug("Type: {}, COT: {}, ASDU: {}".format(self.type_id, self.cot, self.addr))

        self.objs = []
        # has more info objects
        if not sq:
            for i in range(sq_count):
                obj = InfoObjMeta.types[self.type_id](self.asdu)
                # obj = InfoObjMeta.types[self.type_id](data)
                self.objs.append(obj)

        # has one info object
        else:
            for i in range(sq_count):
                obj = InfoObjMeta.types[self.type_id](self.asdu)
                # obj = InfoObjMeta.types[self.type_id](data)
                self.objs.append(obj)
            pass

        self.obj_elements = []


class QDS(object):
    def __init__(self, data):
        overflow = bool(data & 0x01)
        blocked = bool(data & 0x10)
        substituted = bool(data & 0x20)
        not_topical = bool(data & 0x40)
        invalid = bool(data & 0x80)


class InfoObjMeta(type):
    types = {}

    def __new__(mcs, name, bases, dct):
        re = type.__new__(mcs, name, bases, dct)
        if 'type_id' in dct:
            InfoObjMeta.types[dct['type_id']] = re
        return re


class InfoObj(metaclass=InfoObjMeta):

    def __init__(self, unpacked_data):
        self.ioa = (unpacked_data[1] << 8) + unpacked_data[0]
        special_uses = (unpacked_data[2] << 16) + (unpacked_data[1] << 8) + unpacked_data[0]
        # unpacked_data.read("int:16")
        value = unpacked_data
        print("IOA: ", self.ioa)


class SIQ(InfoObj):
    def __init__(self, unpacked_data):
        super(SIQ, self).__init__(unpacked_data)
        self.iv = unpacked_data[0] & 128
        self.nt = unpacked_data[0] & 64
        self.sb = unpacked_data[0] & 32
        self.bl = unpacked_data[0] & 16
        # ...._XXX. - reserve
        self.spi = unpacked_data[0] & 1


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

    def __init__(self, unpacked_data):
        super(MMeNc1, self).__init__(unpacked_data)
        # print(binascii.hexlify(unpacked_data.bytes))
        if isinstance(unpacked_data, tuple):
            pass
        else:
            unpacked_data = struct.unpack("B" * len(unpacked_data), unpacked_data)
        val = ((unpacked_data[3] << 24) +
               (unpacked_data[2] << 16) +
               (unpacked_data[1] << 8) +
               unpacked_data[0])
        # val = unpacked_data.read("floatle:32")

        #qds = QDS(struct.unpack_from('B', data[7:])[0])

        print("val", val)


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
