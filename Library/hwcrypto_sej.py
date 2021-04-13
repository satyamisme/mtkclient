#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (c) B.Kerler 2018-2021 MIT License
import logging, os
from struct import pack, unpack
from Library.utils import LogBase


def bytes_to_dwords(buf):
    res = []
    for i in range(0, len(buf) // 4):
        res.append(unpack("<I", buf[i * 4:(i * 4) + 4])[0])
    return res


regval = {
    "HACC_CON": 0x0000,
    "HACC_ACON": 0x0004,
    "HACC_ACON2": 0x0008,
    "HACC_ACONK": 0x000C,
    "HACC_ASRC0": 0x0010,
    "HACC_ASRC1": 0x0014,
    "HACC_ASRC2": 0x0018,
    "HACC_ASRC3": 0x001C,
    "HACC_AKEY0": 0x0020,
    "HACC_AKEY1": 0x0024,
    "HACC_AKEY2": 0x0028,
    "HACC_AKEY3": 0x002C,
    "HACC_AKEY4": 0x0030,
    "HACC_AKEY5": 0x0034,
    "HACC_AKEY6": 0x0038,
    "HACC_AKEY7": 0x003C,
    "HACC_ACFG0": 0x0040,
    "HACC_ACFG1": 0x0044,
    "HACC_ACFG2": 0x0048,
    "HACC_ACFG3": 0x004C,
    "HACC_AOUT0": 0x0050,
    "HACC_AOUT1": 0x0054,
    "HACC_AOUT2": 0x0058,
    "HACC_AOUT3": 0x005C,
    "HACC_SW_OTP0": 0x0060,
    "HACC_SW_OTP1": 0x0064,
    "HACC_SW_OTP2": 0x0068,
    "HACC_SW_OTP3": 0x006c,
    "HACC_SW_OTP4": 0x0070,
    "HACC_SW_OTP5": 0x0074,
    "HACC_SW_OTP6": 0x0078,
    "HACC_SW_OTP7": 0x007c,
    "HACC_SECINIT0": 0x0080,
    "HACC_SECINIT1": 0x0084,
    "HACC_SECINIT2": 0x0088,
    "HACC_MKJ": 0x00a0
}


class hacc_reg:
    def __init__(self, mtk):
        self.mtk = mtk
        self.sej_base = mtk.config.chipconfig.sej_base
        self.read32 = self.mtk.preloader.read32
        self.write32 = self.mtk.preloader.write32

    def __setattr__(self, key, value):
        if key in ("mtk", "sej_base", "read32", "write32", "regval"):
            return super(hacc_reg, self).__setattr__(key, value)
        if key in regval:
            addr = regval[key] + self.sej_base
            return self.write32(addr, value)
        else:
            return super(hacc_reg, self).__setattr__(key, value)

    def __getattribute__(self, item):
        if item in ("mtk", "sej_base", "read32", "write32", "regval"):
            return super(hacc_reg, self).__getattribute__(item)
        if item in regval:
            addr = regval[item] + self.sej_base
            return self.read32(addr)
        else:
            return super(hacc_reg, self).__getattribute__(item)


class sej(metaclass=LogBase):
    encrypt = True

    HACC_AES_DEC = 0x00000000
    HACC_AES_ENC = 0x00000001
    HACC_AES_MODE_MASK = 0x00000002
    HACC_AES_ECB = 0x00000000
    HACC_AES_CBC = 0x00000002
    HACC_AES_TYPE_MASK = 0x00000030
    HACC_AES_128 = 0x00000000
    HACC_AES_192 = 0x00000010
    HACC_AES_256 = 0x00000020
    HACC_AES_CHG_BO_MASK = 0x00001000
    HACC_AES_CHG_BO_OFF = 0x00000000
    HACC_AES_CHG_BO_ON = 0x00001000
    HACC_AES_START = 0x00000001
    HACC_AES_CLR = 0x00000002
    HACC_AES_RDY = 0x00008000

    HACC_AES_BK2C = 0x00000010
    HACC_AES_R2K = 0x00000100

    HACC_SECINIT0_MAGIC = 0xAE0ACBEA
    HACC_SECINIT1_MAGIC = 0xCD957018
    HACC_SECINIT2_MAGIC = 0x46293911

    # This seems to be fixed
    g_CFG_RANDOM_PATTERN = [
        0x2D44BB70,
        0xA744D227,
        0xD0A9864B,
        0x83FFC244,
        0x7EC8266B,
        0x43E80FB2,
        0x01A6348A,
        0x2067F9A0,
        0x54536405,
        0xD546A6B1,
        0x1CC3EC3A,
        0xDE377A83
    ]

    g_HACC_CFG_1 = [
        0x9ED40400, 0x00E884A1, 0xE3F083BD, 0x2F4E6D8A,
        0xFF838E5C, 0xE940A0E3, 0x8D4DECC6, 0x45FC0989
    ]

    g_HACC_CFG_2 = [
        0xAA542CDA, 0x55522114, 0xE3F083BD, 0x55522114,
        0xAA542CDA, 0xAA542CDA, 0x55522114, 0xAA542CDA
    ]

    g_HACC_CFG_3 = [
        0x2684B690, 0xEB67A8BE, 0xA113144C, 0x177B1215,
        0x168BEE66, 0x1284B684, 0xDF3BCE3A, 0x217F6FA2
    ]

    def __init__(self, mtk, loglevel=logging.INFO):
        self.mtk = mtk
        self.__logger = self.__logger
        self.hwcode = self.mtk.config.hwcode
        self.reg = hacc_reg(mtk)
        # mediatek,hacc, mediatek,sej
        self.sej_base = self.mtk.config.chipconfig.sej_base
        self.read32 = self.mtk.preloader.read32
        self.write32 = self.mtk.preloader.write32
        self.info = self.__logger.info
        if loglevel == logging.DEBUG:
            logfilename = os.path.join("logs", "log.txt")
            if os.path.exists(logfilename):
                os.remove(logfilename)
            fh = logging.FileHandler(logfilename)
            self.__logger.addHandler(fh)
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger.setLevel(logging.INFO)

    def SEJ_V3_Init(self, encrypt=True, g_AC_CFG=None):
        if g_AC_CFG is None:
            g_AC_CFG = self.g_HACC_CFG_1
        acon_setting = self.HACC_AES_CHG_BO_OFF | self.HACC_AES_CBC | self.HACC_AES_128
        if encrypt:
            acon_setting |= self.HACC_AES_ENC
        else:
            acon_setting |= self.HACC_AES_DEC

        # clear key
        self.reg.HACC_AKEY0 = 0
        self.reg.HACC_AKEY1 = 0
        self.reg.HACC_AKEY2 = 0
        self.reg.HACC_AKEY3 = 0
        self.reg.HACC_AKEY4 = 0
        self.reg.HACC_AKEY5 = 0
        self.reg.HACC_AKEY6 = 0
        self.reg.HACC_AKEY7 = 0

        # Generate META Key
        self.reg.HACC_ACON = self.HACC_AES_CHG_BO_OFF | self.HACC_AES_CBC | self.HACC_AES_128 | self.HACC_AES_DEC

        # init ACONK, bind HUID/HUK to HACC, this may differ
        # enable R2K, so that output data is feedback to key by HACC internal algorithm
        self.reg.HACC_ACONK = self.HACC_AES_BK2C | self.HACC_AES_R2K

        # clear HACC_ASRC/HACC_ACFG/HACC_AOUT
        self.reg.HACC_ACON2 = self.HACC_AES_CLR
        self.reg.HACC_ACFG0 = g_AC_CFG[0]
        self.reg.HACC_ACFG1 = g_AC_CFG[1]
        self.reg.HACC_ACFG2 = g_AC_CFG[2]
        self.reg.HACC_ACFG3 = g_AC_CFG[3]

        # encrypt fix pattern 3 rounds to generate a pattern from HUID/HUK
        for i in range(0, 3):
            pos = i * 4
            self.reg.HACC_ASRC0 = self.g_CFG_RANDOM_PATTERN[pos]
            self.reg.HACC_ASRC1 = self.g_CFG_RANDOM_PATTERN[pos + 1]
            self.reg.HACC_ASRC2 = self.g_CFG_RANDOM_PATTERN[pos + 2]
            self.reg.HACC_ASRC3 = self.g_CFG_RANDOM_PATTERN[pos + 3]
            self.reg.HACC_ACON2 = self.HACC_AES_START
            while True:
                if self.reg.HACC_ACON2 & self.HACC_AES_RDY != 0:
                    break
        self.reg.HACC_ACON2 = self.HACC_AES_CLR
        self.reg.HACC_ACFG0 = g_AC_CFG[0]
        self.reg.HACC_ACFG1 = g_AC_CFG[1]
        self.reg.HACC_ACFG2 = g_AC_CFG[2]
        self.reg.HACC_ACFG3 = g_AC_CFG[3]
        self.reg.HACC_ACON = acon_setting
        self.reg.HACC_ACONK = 0

    def SEJ_V3_Terminate(self):
        self.reg.HACC_ACON2 = self.HACC_AES_CLR
        self.reg.HACC_AKEY0 = 0
        self.reg.HACC_AKEY1 = 0
        self.reg.HACC_AKEY2 = 0
        self.reg.HACC_AKEY3 = 0
        self.reg.HACC_AKEY4 = 0
        self.reg.HACC_AKEY5 = 0
        self.reg.HACC_AKEY6 = 0
        self.reg.HACC_AKEY7 = 0

    def SEJ_V3_Run(self, data):
        pdst = bytearray()
        psrc = bytes_to_dwords(data)
        plen = len(psrc)
        pos = 0
        for i in range(plen // 4):
            self.reg.HACC_ASRC0 = psrc[pos + 0]
            self.reg.HACC_ASRC1 = psrc[pos + 1]
            self.reg.HACC_ASRC2 = psrc[pos + 2]
            self.reg.HACC_ASRC3 = psrc[pos + 3]
            self.reg.HACC_ACON2 = 1
            while True:
                if self.reg.HACC_ACON2 & self.HACC_AES_RDY != 0:
                    break
            pdst.extend(pack("<I", self.reg.HACC_AOUT0))
            pdst.extend(pack("<I", self.reg.HACC_AOUT1))
            pdst.extend(pack("<I", self.reg.HACC_AOUT2))
            pdst.extend(pack("<I", self.reg.HACC_AOUT3))
        return pdst

    def hw_aes128_cbc_encrypt(self, buf, encrypt=True):
        self.info("HACC init")
        self.SEJ_V3_Init(encrypt)
        self.info("HACC run")
        buf2 = self.SEJ_V3_Run(buf)
        self.info("HACC terminate")
        self.SEJ_V3_Terminate()
        return buf2
