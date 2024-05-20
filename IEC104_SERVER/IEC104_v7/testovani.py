import math
import struct
import time
from datetime import datetime
from ASDU import *

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

    dotaz_cteni_102 = b'\x66\x01\x05\x00\x01\x00\x01\x00\x00'
    # hodnota ve floating point
    merena_teplota_13 = b'\x0D\x81\x05\x00\x01\x00\x01\x00\x00\x42\xF6\x00\x11\x30'
    # aktivace
    povel_aktivace_45 = b'\x2D\x01\x06\x00\x01\x00\x02\x00\x00\x01'
    # deaktivace
    povel_deaktivace_45 = b'\x2D\x01\x08\x00\x01\x00\x02\x00\x00\x01'

    povel_potvrzeni_aktivace_45 = b'\x2D\x01\x07\x00\x01\x00\x02\x00\x00\x01'
    povel_potvrzeni_deaktivace_45 = b'\x2D\x01\x09\x00\x01\x00\x02\x00\x00\x00'

    # o_data = ASDU(povel_potvrzeni_aktivace_45)
    # # new_data = MMeNc1(75.5)
    # print(o_data)
    # # M_ME_NC_1
    # obj = MMeNc1()
    # obj.set_value(75.5)
    # print(obj.values())
    dt_obj = datetime.strptime("2021-08-05 15:25:56.792554",
                               "%Y-%m-%d %H:%M:%S.%f")
    # dt_ob = datetime.strptime(__format="%Y-%m-%d %H:%M:%S.%f")
    # Verify the value for nano seconds
    # print(time.strftime(format=""))
    nano_secs = dt_obj.strftime("%f")
    print(nano_secs)

    now = datetime.now().strftime("%H:%M:%S:%f")
    print(now)

    # print(datetime.strftime("%f"))
