#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (c) B.Kerler 2018-2021 MIT License
import logging
import os
from Library.utils import LogBase
from Library.error import ErrorHandler
from Library.daconfig import DAconfig
from Library.mtk_dalegacy import DALegacy
from Library.mtk_daxflash import DAXFlash
from config.brom_config import damodes


class DAloader(metaclass=LogBase):
    def __init__(self, mtk, loader=None, preloader=None, loglevel=logging.INFO):
        self.mtk = mtk
        self.__logger = self.__logger
        self.blver = 1
        self.loader = loader
        self.preloader = preloader
        self.loglevel = loglevel
        self.eh = ErrorHandler()
        self.config = self.mtk.config
        self.info = self.__logger.info
        self.error = self.__logger.error
        self.warning = self.__logger.warning
        self.usbwrite = self.mtk.port.usbwrite
        self.usbread = self.mtk.port.usbread
        self.echo = self.mtk.port.echo
        self.rbyte = self.mtk.port.rbyte
        self.rdword = self.mtk.port.rdword
        self.rword = self.mtk.port.rword
        self.daconfig = DAconfig(self.mtk, loader, preloader, loglevel)
        self.da = None
        if loglevel == logging.DEBUG:
            logfilename = os.path.join("logs", "log.txt")
            if os.path.exists(logfilename):
                os.remove(logfilename)
            fh = logging.FileHandler(logfilename)
            self.__logger.addHandler(fh)
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger.setLevel(logging.INFO)

    def set_da(self):
        if self.config.chipconfig.damode == damodes.DEFAULT:
            self.da = DALegacy(self.mtk, self.daconfig, self.loglevel)
        else:
            self.da = DAXFlash(self.mtk, self.daconfig, self.loglevel)

    def detect_partition(self, arguments, partitionname, parttype=None):
        fpartitions = []
        data, guid_gpt = self.da.partition.get_gpt(int(arguments["--gpt-num-part-entries"]),
                                                   int(arguments["--gpt-part-entry-size"]),
                                                   int(arguments["--gpt-part-entry-start-lba"]), parttype)
        if guid_gpt is None:
            return [False, fpartitions]
        else:
            for partition in guid_gpt.partentries:
                fpartitions.append(partition)
                if partition.name.lower() == partitionname.lower():
                    return [True, partition]
        return [False, fpartitions]

    def get_gpt(self, arguments, parttype=None):
        fpartitions = []
        data, guid_gpt = self.da.partition.get_gpt(int(arguments["--gpt-num-part-entries"]),
                                                   int(arguments["--gpt-part-entry-size"]),
                                                   int(arguments["--gpt-part-entry-start-lba"]), parttype)
        if guid_gpt is None:
            return [False, fpartitions]
        return [data, guid_gpt]

    def upload(self):
        return self.da.upload()

    def close(self):
        return self.da.close()

    def upload_da(self):
        self.daconfig.setup()
        self.set_da()
        return self.da.upload_da()

    def writeflash(self, addr, length, filename, partitionname, parttype, display=True):
        return self.da.writeflash(addr=addr, length=length, filename=filename, partitionname=partitionname, parttype=parttype, display=display)

    def formatflash(self, addr, length, partitionname, parttype, display=True):
        return self.da.formatflash(addr=addr, length=length, parttype=parttype)

    def readflash(self, addr, length, filename, parttype, display=True):
        return self.da.readflash(addr=addr, length=length, filename=filename, parttype=parttype, display=display)
