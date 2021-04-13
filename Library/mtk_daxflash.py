#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (c) B.Kerler 2018-2021 MIT License
import logging
import time
import os
from binascii import hexlify
from struct import pack, unpack
from Library.utils import LogBase, print_progress
from Library.error import ErrorHandler
from Library.daconfig import PartitionType, DaStorage
from Library.partition import Partition


class DAXFlash(metaclass=LogBase):
    class Cmd:
        MAGIC = 0xFEEEEEEF
        UNKNOWN = 0x010000
        DOWNLOAD = 0x010001
        UPLOAD = 0x010002
        FORMAT = 0x010003
        WRITE_DATA = 0x010004
        READ_DATA = 0x010005
        FORMAT_PARTITION = 0x010006
        SHUTDOWN = 0x010007
        BOOT_TO = 0x010008
        DEVICE_CTRL = 0x010009
        INIT_EXT_RAM = 0x01000A
        SWITCH_USB_SPEED = 0x01000B
        READ_OTP_ZONE = 0x01000C
        WRITE_OTP_ZONE = 0x01000D
        WRITE_EFUSE = 0x01000E
        READ_EFUSE = 0x01000F
        NAND_BMT_REMARK = 0x010010
        SETUP_ENVIRONMENT = 0x010100
        SETUP_HW_INIT_PARAMS = 0x010101

        SYNC_SIGNAL = 0x434E5953

        UNKNOWN_CTRL_CODE = 0x090000
        CTRL_STORAGE_TEST = 0x090001
        CTRL_RAM_TEST = 0x090002

        GET_EMMC_INFO = 0x040001
        GET_NAND_INFO = 0x040002
        GET_NOR_INFO = 0x040003
        GET_UFS_INFO = 0x040004
        GET_VERSION = 0x040005
        GET_EXPIRE_DATA = 0x040006
        GET_PACKET_LENGTH = 0x040007
        GET_RANDOM_ID = 0x040008
        GET_PARTITION_TBL_CATA = 0x040009
        GET_CONNECTION_AGENT = 0x04000A
        GET_USB_SPEED = 0x04000B
        GET_RAM_INFO = 0x04000C
        GET_CHIP_ID = 0x04000D
        GET_OTP_LOCK_STATUS = 0x04000E
        GET_BATTERY_VOLTAGE = 0x04000F
        GET_RPMB_STATUS = 0x040010
        GET_EXPIRE_DATE = 0x040011
        GET_DRAM_TYPE = 0x040012
        GET_DEV_FW_INFO = 0x040013

        SET_BMT_PERCENTAGE = 0x020001
        SET_BATTERY_OPT = 0x020002
        SET_CHECKSUM_LEVEL = 0x020003
        SET_RESET_KEY = 0x020004
        SET_HOST_INFO = 0x020005
        SET_META_BOOT_MODE = 0x020006
        SET_EMMC_HWRESET_PIN = 0x020007
        SET_GENERATE_GPX = 0x020008
        SET_REGISTER_VALUE = 0x020009
        SET_EXTERNAL_SIG = 0x02000A
        SET_REMOTE_SEC_POLICY = 0x02000B
        SET_ALL_IN_ONE_SIG = 0x02000C
        SET_RSC_INFO = 0x02000D
        SET_UPDATE_FW = 0x020010
        SET_UFS_CONFIG = 0x020011

        START_DL_INFO = 0x080001
        END_DL_INFO = 0x080002
        ACT_LOCK_OTP_ZONE = 0x080003
        DISABLE_EMMC_HWRESET_PIN = 0x080004
        DA_STOR_LIFE_CYCLE_CHECK = 0x080007

        DEVICE_CTRL_READ_REGISTER = 0x0E0003
        CC_OPTIONAL_DOWNLOAD_ACT = 0x800005

    class ChecksumAlgorithm:
        PLAIN = 0
        CRC32 = 1
        MD5 = 2

    class FtSystemOSE:
        OS_WIN = 0
        OS_LINUX = 1

    class DataType:
        DT_PROTOCOL_FLOW = 1
        DT_MESSAGE = 2

    def __init__(self, mtk, daconfig, loglevel=logging.INFO):
        self.mtk = mtk
        self.sram = None
        self.dram = None
        self.emmc = None
        self.nand = None
        self.nor = None
        self.ufs = None
        self.chipid = None
        self.randomid = None
        self.__logger = self.__logger
        self.blver = 1
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
        self.daconfig = daconfig
        self.partition = Partition(self.mtk, self.readflash, self.read_pmt, loglevel)

        if loglevel == logging.DEBUG:
            logfilename = os.path.join("logs", "log.txt")
            if os.path.exists(logfilename):
                os.remove(logfilename)
            fh = logging.FileHandler(logfilename)
            self.__logger.addHandler(fh)
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger.setLevel(logging.INFO)

    def ack(self):
        tmp = pack("<III", self.Cmd.MAGIC, self.DataType.DT_PROTOCOL_FLOW, 4)
        data = pack("<I", 0)
        if self.usbwrite(tmp):
            return self.usbwrite(data)

    def send(self, data, datatype=DataType.DT_PROTOCOL_FLOW):
        if isinstance(data, int):
            data = pack("<I", data)
            length = 4
        else:
            length = len(data)
        tmp = pack("<III", self.Cmd.MAGIC, datatype, length)
        if self.usbwrite(tmp):
            return self.usbwrite(data)
        return False

    def recv(self):
        magic, datatype, length = unpack("<III", self.usbread(4 + 4 + 4))
        resp = self.usbread(length, 512)
        return resp

    def rdword(self, count=1):
        data = []
        for i in range(count):
            data.append(unpack("<I", self.recv())[0])
        if count == 1:
            return data[0]
        return data

    def status(self):
        status = unpack("<I", self.recv())[0]
        return status

    def read_pmt(self):
        return b"", []

    def send_param(self, params):
        if isinstance(params, bytes):
            params = [params]
        for param in params:
            pkt = pack("<III", self.Cmd.MAGIC, self.DataType.DT_PROTOCOL_FLOW, len(param))
            if self.usbwrite(pkt):
                time.sleep(0.05)
                length = len(param)
                pos = 0
                while length > 0:
                    dsize = min(length, 0x200)
                    if not self.usbwrite(param[pos:pos + dsize]):
                        break
                    pos += dsize
                    length -= dsize
        status = self.status()
        if status == 0:
            return True
        else:
            self.error(f"Error on sending parameter, status {hex(status)}.")
        return False

    def send_devctrl(self, cmd, param=None, status=None):
        if status is None:
            status = [0]
        if self.send(self.Cmd.DEVICE_CTRL):
            status[0] = self.status()
            if status[0] == 0x0:
                if self.send(cmd):
                    status[0] = self.status()
                    if status[0] == 0x0:
                        if param is None:
                            return self.recv()
                        else:
                            return self.send_param(param)
        self.error("Error on sending dev ctrl 0x%X, status 0x%X" % (cmd, status[0]))
        return b""

    def set_reset_key(self, reset_key=0x68):
        # default:0x0,one:0x50,two:0x68
        param = pack("<I", reset_key)
        return self.send_devctrl(self.Cmd.SET_RESET_KEY, param)

    def set_checksum_level(self, checksum_level=0x0):
        param = pack("<I", checksum_level)
        # none[0x0]. USB[0x1]. storage[0x2], both[0x3]
        return self.send_devctrl(self.Cmd.SET_CHECKSUM_LEVEL, param)

    def set_battery_opt(self, option=0x2):
        param = pack("<I", option)
        # battery[0x0]. USB power[0x1]. auto[0x2]
        return self.send_devctrl(self.Cmd.SET_BATTERY_OPT, param)

    def send_emi(self, emi):
        if self.send(self.Cmd.INIT_EXT_RAM):
            if self.status() == 0:
                if self.send(pack("<I", len(emi))):
                    return self.send_param(emi)
        return False

    def send_data(self, data):
        pkt2 = pack("<III", self.Cmd.MAGIC, self.DataType.DT_PROTOCOL_FLOW, len(data))
        if self.usbwrite(pkt2):
            bytestowrite = len(data)
            pos = 0
            while bytestowrite > 0:
                if self.usbwrite(data[pos:pos + 64]):
                    pos += 64
                    bytestowrite -= 64
            status = self.status()
            if status == 0x0:
                return True
            else:
                self.error(f"Error on sending data: {hex(status)}")
                return False

    def boot_to(self, at_address, da):  # =0x40000000
        if self.send(self.Cmd.BOOT_TO):
            if self.status() == 0:
                param = pack("<QQ", at_address, len(da))
                pkt1 = pack("<III", self.Cmd.MAGIC, self.DataType.DT_PROTOCOL_FLOW, len(param))
                if self.usbwrite(pkt1):
                    if self.usbwrite(param):
                        if self.send_data(da):
                            time.sleep(0.5)
                            status = self.status()
                            if status == 0x434E5953:
                                return True
        return False

    def get_connection_agent(self):
        # brom
        res = self.send_devctrl(self.Cmd.GET_CONNECTION_AGENT)
        status = self.status()
        if status == 0x0:
            return res

    def formatflash(self, addr, length, storage=DaStorage.MTK_DA_STORAGE_EMMC,
                    parttype=PartitionType.MTK_DA_EMMC_PART_USER, display=False):
        if parttype is None or parttype == "user":
            parttype = PartitionType.MTK_DA_EMMC_PART_USER
        elif parttype == "boot1":
            parttype = PartitionType.MTK_DA_EMMC_PART_BOOT1
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.boot1_size)
        elif parttype == "boot2":
            parttype = PartitionType.MTK_DA_EMMC_PART_BOOT2
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.boot2_size)
        elif parttype == "gp1":
            parttype = PartitionType.MTK_DA_EMMC_PART_GP1
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.gp1_size)
        elif parttype == "gp2":
            parttype = PartitionType.MTK_DA_EMMC_PART_GP2
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.gp2_size)
        elif parttype == "gp3":
            parttype = PartitionType.MTK_DA_EMMC_PART_GP3
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.gp3_size)
        elif parttype == "gp4":
            parttype = PartitionType.MTK_DA_EMMC_PART_GP4
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.gp4_size)
        elif parttype == "rpmb":
            parttype = PartitionType.MTK_DA_EMMC_PART_RPMB
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.rpmb_size)
        else:
            self.error("Unknown parttype. Known parttypes are \"boot1\",\"boot2\",\"gp1\"," +
                       "\"gp2\",\"gp3\",\"gp4\",\"rpmb\"")
            return False
        if self.send(self.Cmd.FORMAT):
            if self.status() == 0:
                # storage: emmc:1,slc,nand,nor,ufs
                # section: boot,user of emmc:8, LU1, LU2
                class NandExtension:
                    # uni=0, multi=1
                    cellusage = 0
                    # logical=0, physical=1, physical_pmt=2
                    addr_type = 0
                    # raw=0, ubi_img=1, ftl_img=2
                    bin_type = 0
                    # operation_type -> spare=0,page=1,page_ecc=2,page_spare_ecc=3,verify=4,page_spare_norandom,page_fdm
                    # nand_format_level -> format_normal=0,force=1,mark_bad_block=2,level_end=3
                    operation_type = 0  # or nand_format_level
                    sys_slc_percent = 0
                    usr_slc_percent = 0
                    phy_max_size = 0

                ne = NandExtension()
                param = pack("<IIQQ", storage, parttype, addr, length)
                param += pack("<IIIIIIII", ne.cellusage, ne.addr_type, ne.bin_type, ne.operation_type,
                              ne.sys_slc_percent, ne.usr_slc_percent, ne.phy_max_size, 0x0)
                self.send_param(param)
                status = self.status()
                if status == 0x0:
                    return True
        return False

    def get_chip_id(self):
        class Chipid:
            hw_code = 0
            hw_sub_code = 0
            hw_version = 0
            sw_version = 0
            chip_evolution = 0

        cid = Chipid
        data = self.send_devctrl(self.Cmd.GET_CHIP_ID)
        cid.hw_code, cid.hw_sub_code, cid.hw_version, cid.sw_version, cid.chip_evolution = unpack(">HHHHH",
                                                                                                  data[:(5 * 2)])
        if self.status() == 0:
            return cid
        return None

    def get_ram_info(self):
        resp = self.send_devctrl(self.Cmd.GET_RAM_INFO)
        if self.status() == 0x0:
            class RamInfo:
                type = 0
                base_address = 0
                size = 0

            sram = RamInfo()
            dram = RamInfo()
            sram.type, sram.base_address, sram.size, dram.type, dram.base_address, dram.size = unpack("<IIIIII",
                                                                                                      resp[:24])
            return sram, dram
        return None, None

    def get_emmc_info(self):
        resp = self.send_devctrl(self.Cmd.GET_EMMC_INFO)
        if self.status() == 0:
            class EmmcInfo:
                type = 1  # emmc or sdmmc or none
                block_size = 0x200
                boot1_size = 0
                boot2_size = 0
                rpmb_size = 0
                gp1_size = 0
                gp2_size = 0
                gp3_size = 0
                gp4_size = 0
                user_size = 0
                cid = b""
                fwver = 0
                unknown = b""

            emmc = EmmcInfo()
            pos = 0
            emmc.type, emmc.block_size = unpack("<II", resp[pos:pos + 8])
            pos += 8
            emmc.boot1_size, emmc.boot2_size, emmc.rpmb_size, emmc.gp1_size, emmc.gp2_size, emmc.gp3_size, \
            emmc.gp4_size, emmc.user_size = unpack("<QQQQQQQQ", resp[pos:pos + (8 * 8)])
            pos += 8 * 8
            emmc.cid = resp[pos:pos + (4 * 4)]
            pos += (4 * 4)
            emmc.fwver = unpack("<Q", resp[pos:pos + 8])[0]
            pos += 8
            emmc.unknown = resp[pos:]
            return emmc
        return None

    def get_nand_info(self):
        resp = self.send_devctrl(self.Cmd.GET_NAND_INFO)
        if self.status() == 0:
            class NandInfo:
                type = 1  # slc, mlc, spi, none
                page_size = 0
                block_size = 0x200
                spare_size = 0
                total_size = 0
                available_size = 0
                nand_bmt_exist = 0
                nand_id = 0

            nand = NandInfo()
            pos = 0
            nand.type, nand.page_size, nand.block_size, nand.spare_size = unpack("<IIII", resp[pos:pos + 16])
            pos += 16
            nand.total_size, nand.available_size = unpack("<QQ", resp[pos:pos + (2 * 8)])
            pos += 2 * 8
            nand.nand_bmt_exist = resp[pos:pos + 1]
            pos += 1
            nand.nand_id = unpack("<12B", resp[pos:pos + 12])
            return nand
        return None

    def get_nor_info(self):
        resp = self.send_devctrl(self.Cmd.GET_NOR_INFO)
        if self.status() == 0:
            class NorInfo:
                type = 1  # nor, none
                page_size = 0
                available_size = 0

            nor = NorInfo()
            nor.type, nor.page_size, nor.available_size = unpack("<IIQ", resp[:16])
            return nor
        return None

    def get_ufs_info(self):
        resp = self.send_devctrl(self.Cmd.GET_UFS_INFO)
        if self.status() == 0:
            class UfsInfo:
                type = 1  # nor, none
                block_size = 0
                lu0_size = 0
                lu1_size = 0
                lu2_size = 0
                cid = b""
                fwver = 0

            ufs = UfsInfo()
            ufs.type, ufs.block_size, ufs.lu0_size, ufs.lu1_size, ufs.lu2_size = unpack("<IIQQQ",
                                                                                        resp[:(2 * 4) + (3 * 8)])
            pos = (2 * 4) + (3 * 8)
            ufs.cid = resp[pos:pos + 16]
            ufs.fwver = unpack("<I", resp[pos + 16:pos + 16 + 4])[0]
            return ufs
        return None

    def get_expire_date(self):
        res = self.send_devctrl(self.Cmd.GET_EXPIRE_DATE)
        if res != b"":
            if self.status() == 0x0:
                return res
        return None

    def get_random_id(self):
        res = self.send_devctrl(self.Cmd.GET_RANDOM_ID)
        if self.status() == 0:
            return res
        return None

    def get_da_stor_life_check(self):
        res = self.send_devctrl(self.Cmd.DA_STOR_LIFE_CYCLE_CHECK)
        return unpack("<I", res)[0]

    def get_packet_length(self):
        resp = self.send_devctrl(self.Cmd.GET_PACKET_LENGTH)
        status = self.status()
        if status == 0:
            class Packetlen:
                write_packet_length = 0
                read_packet_length = 0

            plen = Packetlen()
            plen.write_packet_length, plen.read_packet_length = unpack("<II", resp)
            return plen
        return None

    def cmd_read_data(self, addr, size, storage=DaStorage.MTK_DA_STORAGE_EMMC,
                      parttype=PartitionType.MTK_DA_EMMC_PART_USER):
        if self.send(self.Cmd.READ_DATA):
            if self.status() == 0:
                # storage: emmc:1,slc,nand,nor,ufs
                # section: boot,user of emmc:8, LU1, LU2
                class NandExtension:
                    # uni=0, multi=1
                    cellusage = 0
                    # logical=0, physical=1, physical_pmt=2
                    addr_type = 0
                    # raw=0, ubi_img=1, ftl_img=2
                    bin_type = 0
                    # operation_type -> spare=0,page=1,page_ecc=2,page_spare_ecc=3,verify=4,page_spare_norandom,page_fdm
                    # nand_format_level -> format_normal=0,force=1,mark_bad_block=2,level_end=3
                    operation_type = 0  # or nand_format_level
                    sys_slc_percent = 0
                    usr_slc_percent = 0
                    phy_max_size = 0

                ne = NandExtension()
                param = pack("<IIQQ", storage, parttype, addr, size)
                param += pack("<IIIIIIII", ne.cellusage, ne.addr_type, ne.bin_type, ne.operation_type,
                              ne.sys_slc_percent, ne.usr_slc_percent, ne.phy_max_size, 0x0)
                self.send_param(param)
                status = self.status()
                if status == 0x0:
                    return True
        return False

    def readflash(self, addr, length, filename, parttype=None, display=True):
        if parttype is None or parttype == "user":
            parttype = PartitionType.MTK_DA_EMMC_PART_USER
        elif parttype == "boot1":
            parttype = PartitionType.MTK_DA_EMMC_PART_BOOT1
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.boot1_size)
        elif parttype == "boot2":
            parttype = PartitionType.MTK_DA_EMMC_PART_BOOT2
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.boot2_size)
        elif parttype == "gp1":
            parttype = PartitionType.MTK_DA_EMMC_PART_GP1
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.gp1_size)
        elif parttype == "gp2":
            parttype = PartitionType.MTK_DA_EMMC_PART_GP2
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.gp2_size)
        elif parttype == "gp3":
            parttype = PartitionType.MTK_DA_EMMC_PART_GP3
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.gp3_size)
        elif parttype == "gp4":
            parttype = PartitionType.MTK_DA_EMMC_PART_GP4
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.gp4_size)
        elif parttype == "rpmb":
            parttype = PartitionType.MTK_DA_EMMC_PART_RPMB
            if self.daconfig.flashtype == "emmc":
                length = min(length, self.emmc.rpmb_size)
        else:
            self.error("Unknown parttype. Known parttypes are \"boot1\",\"boot2\",\"gp1\"," +
                       "\"gp2\",\"gp3\",\"gp4\",\"rpmb\"")
            return False

        if self.daconfig.flashtype == "nor":
            storage = DaStorage.MTK_DA_STORAGE_NOR
        elif self.daconfig.flashtype == "nand":
            storage = DaStorage.MTK_DA_STORAGE_NAND
        elif self.daconfig.flashtype == "ufs":
            storage = DaStorage.MTK_DA_STORAGE_UFS
        elif self.daconfig.flashtype == "sdc":
            storage = DaStorage.MTK_DA_STORAGE_SDMMC
        else:
            storage = DaStorage.MTK_DA_STORAGE_EMMC
        if self.cmd_read_data(addr=addr, size=length, storage=storage, parttype=parttype):
            if display:
                print_progress(0, 100, prefix='Progress:', suffix='Complete', bar_length=50)
            old = 0
            bytestoread = length
            if filename != "":
                try:
                    with open(filename, "wb") as wf:
                        while bytestoread > 0:
                            magic, datatype, slength = unpack("<III", self.usbread(4 + 4 + 4))
                            tmp = self.usbread(slength, 512)
                            bytestoread -= len(tmp)
                            if display:
                                prog = (length - bytestoread) / length * 100
                                if round(prog, 1) > old:
                                    print_progress(prog, 100, prefix='Progress:',
                                                   suffix='Complete, Sector:' + hex(length - bytestoread),
                                                   bar_length=50)
                                    old = round(prog, 1)
                            wf.write(tmp)
                            self.ack()
                            if self.status() != 0:
                                break
                except Exception as err:
                    self.error("Couldn't write to " + filename + ". Error: " + str(err))
                    return False
                if display:
                    print_progress(100, 100, prefix='Progress:', suffix='Complete', bar_length=50)
                return True
            else:
                buffer = bytearray()
                while length > 0:
                    tmp = self.recv()
                    buffer.extend(tmp)
                    self.ack()
                    if self.status() != 0:
                        break
                    if display:
                        prog = (length - bytestoread) / length * 100
                        if round(prog, 1) > old:
                            print_progress(prog, 100, prefix='Progress:',
                                           suffix='Complete, Sector:' + hex(length - bytestoread), bar_length=50)
                            old = round(prog, 1)
                    length -= len(tmp)
                if display:
                    print_progress(100, 100, prefix='Progress:', suffix='Complete', bar_length=50)
                return buffer
        return False

    def close(self):
        if self.send(self.Cmd.SHUTDOWN):
            if self.status() == 0:
                self.mtk.port.close()
                return True
        self.mtk.port.close()
        return False

    def writeflash(self, addr, length, filename, partitionname, parttype=None, display=True):
        """
        if parttype is None or parttype == "user":
            parttype = PartitionType.MTK_DA_EMMC_PART_USER
        elif parttype == "boot1":
            parttype = PartitionType.MTK_DA_EMMC_PART_BOOT1
        elif parttype == "boot2":
            parttype = PartitionType.MTK_DA_EMMC_PART_BOOT2
        elif parttype == "gp1":
            parttype = PartitionType.MTK_DA_EMMC_PART_GP1
        elif parttype == "gp2":
            parttype = PartitionType.MTK_DA_EMMC_PART_GP2
        elif parttype == "gp3":
            parttype = PartitionType.MTK_DA_EMMC_PART_GP3
        elif parttype == "gp4":
            parttype = PartitionType.MTK_DA_EMMC_PART_GP4
        elif parttype == "rpmb":
            parttype = PartitionType.MTK_DA_EMMC_PART_RPMB

        if self.daconfig.flashtype == "nor":
            storage = DaStorage.MTK_DA_STORAGE_NOR
        elif self.daconfig.flashtype == "nand":
            storage = DaStorage.MTK_DA_STORAGE_NAND
        elif self.daconfig.flashtype == "ufs":
            storage = DaStorage.MTK_DA_STORAGE_UFS
        elif self.daconfig.flashtype == "sdc":
            storage = DaStorage.MTK_DA_STORAGE_SDMMC
        else:
            storage = DaStorage.MTK_DA_STORAGE_EMMC
        """
        self.send_devctrl(self.Cmd.START_DL_INFO)
        plen = self.get_packet_length()
        bytestowrite = length
        write_packet_size = plen.write_packet_length
        wsize = min(write_packet_size, length)
        if self.send(self.Cmd.DOWNLOAD):
            if self.status() == 0:
                params = [partitionname, pack("<Q", wsize)]
                if self.send_param(params):
                    try:
                        with open(filename, "rb") as rf:
                            pos = 0
                            while bytestowrite > 0:
                                dsize = min(wsize, bytestowrite)
                                data = bytearray(rf.read(dsize))
                                checksum = sum(data) & 0xFFFF
                                dparams = [pack("<I", 0x0), pack("<I", checksum), data]
                                if not self.send_param(dparams):
                                    self.error("Error on writing pos 0x%08X" % pos)
                                    return False
                                bytestowrite -= dsize
                                pos += dsize
                            if self.status() == 0x0:
                                self.send_devctrl(self.Cmd.CC_OPTIONAL_DOWNLOAD_ACT)
                                return True
                    except Exception as e:
                        self.error(str(e))
                        return False
                else:
                    self.error("Error on sending partition param. Right partition name ?")
        return False

    def sync(self):
        if self.send(self.Cmd.SYNC_SIGNAL):
            return True
        return False

    def setup_env(self):
        if self.send(self.Cmd.SETUP_ENVIRONMENT):
            da_log_level = 2
            log_channel = 1
            system_os = self.FtSystemOSE.OS_LINUX
            ufs_provision = 0x0
            param = pack("<IIIII", da_log_level, log_channel, system_os, ufs_provision, 0x0)
            if self.send_param(param):
                return True
        return False

    def setup_hw_init(self):
        if self.send(self.Cmd.SETUP_HW_INIT_PARAMS):
            param = pack("<I", 0x0)  # No config
            if self.send_param(param):
                return True
        return False

    def upload(self):
        if self.daconfig.da is None:
            self.error("No valid da loader found... aborting.")
            return False
        loader = self.daconfig.loader
        self.config.blver = 1
        if self.config.blver == 1:
            self.info("Uploading stage 1...")
            with open(loader, 'rb') as bootldr:
                # stage 1
                stage = self.config.blver + 1
                offset = self.daconfig.da[stage]["m_buf"]
                size = self.daconfig.da[stage]["m_len"]
                address = self.daconfig.da[stage]["m_start_addr"]
                sig_len = self.daconfig.da[stage]["m_sig_len"]
                bootldr.seek(offset)
                dadata = bootldr.read(size)
                if self.mtk.preloader.send_da(address, size, sig_len, dadata):
                    self.info("Successfully uploaded stage 1, jumping ..")
                    if self.mtk.preloader.jump_da(address):
                        time.sleep(0.5)
                        sync = self.usbread(1)
                        if sync != b"\xC0":
                            self.error("Error on DA sync")
                            return False
                        else:
                            self.sync()
                            self.setup_env()
                            self.setup_hw_init()
                            res = self.recv()
                            if res == pack("<I", self.Cmd.SYNC_SIGNAL):
                                self.info("Successfully received DA sync")
                                return True
                            else:
                                self.error("Error on jumping to DA: " + hexlify(res).decode('utf-8'))
                    else:
                        self.error("Error on jumping to DA.")
                else:
                    self.error("Error on sending DA.")
        return False

    def upload_da(self):
        if self.upload():
            self.get_expire_date()
            self.set_reset_key(0x68)
            self.set_battery_opt(0x2)
            self.set_checksum_level(0x0)
            connagent = self.get_connection_agent()
            blver = None
            if connagent == b"brom":
                blver = 2
                if self.daconfig.preloader is not None:
                    if os.path.exists(self.daconfig.preloader):
                        with open(self.daconfig.preloader, "rb") as rf:
                            data = rf.read()
                            idx = data.rfind(b"MTK_BLOADER_INFO_v")
                            if idx != -1:
                                emi = data[idx:]
                                count = unpack("<I", emi[0x6C:0x70])[0]
                                size = (count * 0xB0) + 0x70
                                emi = emi[:size]
                                if not self.send_emi(emi):
                                    return False
                            else:
                                self.error("Couldn't find emi info in preloader.")
                                return False
                    else:
                        self.error(f"Couldn't open {self.daconfig.preloader} for reading.")
                        return False
                else:
                    self.warning("No preloader given. Operation may fail due to missing dram setup.")
            elif connagent == b"preloader":
                blver = 2
            if blver == 2:
                self.info("Uploading stage 2...")
                with open(self.daconfig.loader, 'rb') as bootldr:
                    stage = blver + 1
                    offset = self.daconfig.da[stage]["m_buf"]
                    size = self.daconfig.da[stage]["m_len"] - self.daconfig.da[stage]["m_sig_len"]
                    address = self.daconfig.da[stage]["m_start_addr"]  # at_address
                    # sig_len = self.daconfig.da[stage]["m_sig_len"]
                    bootldr.seek(offset)
                    dadata = bootldr.read(size)
                    if self.boot_to(address, dadata):
                        self.info("Successfully uploaded stage 2")
                        self.sram, self.dram = self.get_ram_info()
                        self.emmc = self.get_emmc_info()
                        self.nand = self.get_nand_info()
                        self.nor = self.get_nor_info()
                        self.ufs = self.get_ufs_info()
                        if self.emmc.type != 0:
                            self.daconfig.flashtype = "emmc"
                            self.daconfig.flashsize = self.emmc.user_size
                        elif self.nand.type != 0:
                            self.daconfig.flashtype = "nand"
                            self.daconfig.flashsize = self.nand.total_size
                        elif self.nor.type != 0:
                            self.daconfig.flashtype = "nor"
                            self.daconfig.flashsize = self.nor.available_size
                        elif self.ufs.type != 0:
                            self.daconfig.flashtype = "ufs"
                            self.daconfig.flashsize = [self.ufs.lu0_size, self.ufs.lu1_size, self.ufs.lu2_size]
                        self.chipid = self.get_chip_id()
                        self.randomid = self.get_random_id()
                        if self.get_da_stor_life_check() == 0x0:
                            return True
                    else:
                        self.error("Error on booting to da (xflash)")
            else:
                self.error("Didn't get brom connection, got instead: " + hexlify(connagent).decode('utf-8'))
        return False
