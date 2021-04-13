#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (c) B.Kerler 2018-2021 MIT License
import logging
import os
from binascii import hexlify
from struct import unpack
from Library.utils import LogBase, read_object


class Storage:
    MTK_DA_HW_STORAGE_NOR = 0
    MTK_DA_HW_STORAGE_NAND = 1
    MTK_DA_HW_STORAGE_EMMC = 2
    MTK_DA_HW_STORAGE_SDMMC = 3
    MTK_DA_HW_STORAGE_UFS = 4


class DaStorage:
    MTK_DA_STORAGE_EMMC = 0x1
    MTK_DA_STORAGE_SDMMC = 0x2
    MTK_DA_STORAGE_NAND = 0x3
    MTK_DA_STORAGE_NOR = 0x4
    MTK_DA_STORAGE_UFS = 0x5


class PartitionType:
    MTK_DA_EMMC_PART_BOOT1 = 1
    MTK_DA_EMMC_PART_BOOT2 = 2
    MTK_DA_EMMC_PART_RPMB = 3
    MTK_DA_EMMC_PART_GP1 = 4
    MTK_DA_EMMC_PART_GP2 = 5
    MTK_DA_EMMC_PART_GP3 = 6
    MTK_DA_EMMC_PART_GP4 = 7
    MTK_DA_EMMC_PART_USER = 8


class Memory:
    M_EMMC = 1
    M_NAND = 2
    M_NOR = 3


entry_region = [
    ('m_buf', 'I'),
    ('m_len', 'I'),
    ('m_start_addr', 'I'),
    ('m_start_offset', 'I'),
    ('m_sig_len', 'I')]

DA = [
    ('magic', 'H'),
    ('hw_code', 'H'),
    ('hw_sub_code', 'H'),
    ('hw_version', 'H'),
    ('sw_version', 'H'),
    ('reserved1', 'H'),
    ('pagesize', 'H'),
    ('reserved3', 'H'),
    ('entry_region_index', 'H'),
    ('entry_region_count', 'H')
    # vector<entry_region> LoadRegion
]


class DAconfig(metaclass=LogBase):
    def __init__(self, mtk, loader=None, preloader=None, loglevel=logging.INFO):
        self.mtk = mtk
        self.__logger = self.__logger
        self.config = self.mtk.config
        self.info = self.__logger.info
        self.debug = self.__logger.debug
        self.error = self.__logger.error
        self.warning = self.__logger.warning
        self.usbwrite = self.mtk.port.usbwrite
        self.usbread = self.mtk.port.usbread
        self.flashsize = 0
        self.sparesize = 0
        self.readsize = 0
        self.pagesize = 512
        self.da = None
        self.dasetup = []
        self.loader = loader
        self.preloader = preloader
        if loglevel == logging.DEBUG:
            logfilename = os.path.join("logs", "log.txt")
            if os.path.exists(logfilename):
                os.remove(logfilename)
            fh = logging.FileHandler(logfilename)
            self.__logger.addHandler(fh)
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger.setLevel(logging.INFO)

        if loader is None:
            loaders = []
            for root, dirs, files in os.walk("Loader", topdown=False):
                for file in files:
                    if not "Preloader" in root:
                        loaders.append(os.path.join(root, file))
            for loader in loaders:
                self.parse_da_loader(loader)
        else:
            if not os.path.exists(loader):
                self.warning("Couldn't open " + loader)
            else:
                self.parse_da_loader(loader)

    def parse_da_loader(self, loader):
        try:
            with open(loader, 'rb') as bootldr:
                data = bootldr.read()
                self.debug(hexlify(data).decode('utf-8'))
                bootldr.seek(0x68)
                count_da = unpack("<I", bootldr.read(4))[0]
                for i in range(0, count_da):
                    bootldr.seek(0x6C + (i * 0xDC))
                    datmp = read_object(bootldr.read(0x14), DA)  # hdr
                    datmp["loader"] = loader
                    da = [datmp]
                    # bootldr.seek(0x6C + (i * 0xDC) + 0x14) #sections
                    count = datmp["entry_region_count"]
                    for m in range(0, count):
                        entry_tmp = read_object(bootldr.read(20), entry_region)
                        da.append(entry_tmp)
                    self.dasetup.append(da)
                return True
        except Exception as e:
            self.error("Couldn't open loader: " + loader + ". Reason: " + str(e))
        return False

    def setup(self):
        dacode = self.config.chipconfig.dacode
        for setup in self.dasetup:
            if setup[0]["hw_code"] == dacode:
                if setup[0]["hw_version"] <= self.config.hwver:
                    if setup[0]["sw_version"] <= self.config.swver:
                        self.da = setup
                        if self.loader is None:
                            self.loader = self.da[0]["loader"]

        if self.da is None:
            self.error("No da config set up")
        return self.da
