#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (c) B.Kerler 2018-2021 MIT License
import sys
import logging
import os
import time
from struct import pack, unpack
from Library.utils import LogBase, print_progress, read_object
from binascii import hexlify
from Library.error import ErrorHandler
from Library.daconfig import DaStorage, PartitionType
from Library.partition import Partition

norinfo = [
    ('m_nor_ret', '>I'),
    ('m_nor_chip_select', '2B'),
    ('m_nor_flash_id', '>H'),
    ('m_nor_flash_size', '>I'),
    ('m_nor_flash_dev_code', '>4H'),
    ('m_nor_flash_otp_status', '>I'),
    ('m_nor_flash_otp_size', '>I')
]

nandinfo32 = [
    ('m_nand_info', '>I'),
    ('m_nand_chip_select', '>B'),
    ('m_nand_flash_id', '>H'),
    ('m_nand_flash_size', '>I'),
    ('m_nand_flash_id_count', '>H'),
]

nandinfo64 = [
    ('m_nand_info', '>I'),
    ('m_nand_chip_select', '>B'),
    ('m_nand_flash_id', '>H'),
    ('m_nand_flash_size', '>Q'),
    ('m_nand_flash_id_count', '>H'),
]

# ('m_nand_flash_dev_code', '>7H'),

nandinfo2 = [
    ('m_nand_pagesize', '>H'),
    ('m_nand_sparesize', '>H'),
    ('m_nand_pages_per_block', '>H'),
    ('m_nand_io_interface', 'B'),
    ('m_nand_addr_cycle', 'B'),
    ('m_nand_bmt_exist', 'B'),
]

emmcinfo = [
    ('m_emmc_ret', '>I'),
    ('m_emmc_boot1_size', '>Q'),
    ('m_emmc_boot2_size', '>Q'),
    ('m_emmc_rpmb_size', '>Q'),
    ('m_emmc_gp_size', '>4Q'),
    ('m_emmc_ua_size', '>Q'),
    ('m_emmc_cid', '>2Q'),
    ('m_emmc_fwver', '8B')
]

sdcinfo = [
    ('m_sdmmc_info', '>I'),
    ('m_sdmmc_ua_size', '>Q'),
    ('m_sdmmc_cid', '>2Q')
]

configinfo = [
    ('m_int_sram_ret', '>I'),
    ('m_int_sram_size', '>I'),
    ('m_ext_ram_ret', '>I'),
    ('m_ext_ram_type', 'B'),
    ('m_ext_ram_chip_select', 'B'),
    ('m_ext_ram_size', '>Q'),
    ('randomid', '>2Q'),
]

passinfo = [
    ('ack', 'B'),
    ('m_download_status', '>I'),
    ('m_boot_style', '>I'),
    ('soc_ok', 'B')
]


def crc_word(data, chs=0):
    return (sum(data) + chs) & 0xFFFF


class DALegacy(metaclass=LogBase):
    class Rsp:
        SOC_OK = b"\xC1"
        SOC_FAIL = b"\xCF"
        SYNC_CHAR = b"\xC0"
        CONT_CHAR = b"\x69"
        STOP_CHAR = b"\x96"
        ACK = b"\x5A"
        NACK = b"\xA5"
        UNKNOWN_CMD = b"\xBB"

    class PortValues:
        UART_BAUD_921600 = b'\x01',
        UART_BAUD_460800 = b'\x02',
        UART_BAUD_230400 = b'\x03',
        UART_BAUD_115200 = b'\x04',
        UART_BAUD_57600 = b'\x05',
        UART_BAUD_38400 = b'\x06',
        UART_BAUD_19200 = b'\x07',
        UART_BAUD_9600 = b'\x08',
        UART_BAUD_4800 = b'\x09',
        UART_BAUD_2400 = b'\x0a',
        UART_BAUD_1200 = b'\x0b',
        UART_BAUD_300 = b'\x0c',
        UART_BAUD_110 = b'\x0d'

    class Cmd:
        # COMMANDS
        DOWNLOAD_BLOADER_CMD = b"\x51"
        NAND_BMT_REMARK_CMD = b"\x52"

        SDMMC_SWITCH_PART_CMD = b"\x60"
        SDMMC_WRITE_IMAGE_CMD = b"\x61"
        SDMMC_WRITE_DATA_CMD = b"\x62"
        SDMMC_GET_CARD_TYPE = b"\x63"
        SDMMC_RESET_DIS_CMD = b"\x64"

        UFS_SWITCH_PART_CMD = b"\x80"
        UFS_WRITE_IMAGE_CMD = b"\x81"
        UFS_WRITE_DATA_CMD = b"\x82"
        UFS_READ_GPT_CMD = b"\x85"
        UFS_WRITE_GPT_CMD = b"\x89"

        UFS_OTP_CHECKDEVICE_CMD = b"\x8a"
        UFS_OTP_GETSIZE_CMD = b"\x8b"
        UFS_OTP_READ_CMD = b"\x8c"
        UFS_OTP_PROGRAM_CMD = b"\x8d"
        UFS_OTP_LOCK_CMD = b"\x8e"
        UFS_OTP_LOCK_CHECKSTATUS_CMD = b"\x8f"

        USB_SETUP_PORT = b"\x70"
        USB_LOOPBACK = b"\x71"
        USB_CHECK_STATUS = b"\x72"
        USB_SETUP_PORT_EX = b"\x73"

        # EFUSE
        READ_REG32_CMD = b"\x7A"
        WRITE_REG32_CMD = b"\x7B"
        PWR_READ16_CMD = b"\x7C"
        PWR_WRITE16_CMD = b"\x7D"
        PWR_READ8_CMD = b"\x7E"
        PWR_WRITE8_CMD = b"\x7F"

        EMMC_OTP_CHECKDEVICE_CMD = b"\x99"
        EMMC_OTP_GETSIZE_CMD = b"\x9A"
        EMMC_OTP_READ_CMD = b"\x9B"
        EMMC_OTP_PROGRAM_CMD = b"\x9C"
        EMMC_OTP_LOCK_CMD = b"\x9D"
        EMMC_OTP_LOCK_CHECKSTATUS_CMD = b"\x9E"

        WRITE_USB_DOWNLOAD_CONTROL_BIT_CMD = b"\xA0"
        WRITE_PARTITION_TBL_CMD = b"\xA1"
        READ_PARTITION_TBL_CMD = b"\xA2"
        READ_BMT = b"\xA3"
        SDMMC_WRITE_PMT_CMD = b"\xA4"
        SDMMC_READ_PMT_CMD = b"\xA5"
        READ_IMEI_PID_SWV_CMD = b"\xA6"
        READ_DOWNLOAD_INFO = b"\xA7"
        WRITE_DOWNLOAD_INFO = b"\xA8"
        SDMMC_WRITE_GPT_CMD = b"\xA9"
        NOR_READ_PTB_CMD = b"\xAA"
        NOR_WRITE_PTB_CMD = b"\xAB"

        NOR_BLOCK_INDEX_TO_ADDRESS = b"\xB0"  # deprecated
        NOR_ADDRESS_TO_BLOCK_INDEX = b"\xB1"  # deprecated
        NOR_WRITE_DATA = b"\xB2"  # deprecated
        NAND_WRITE_DATA = b"\xB3"
        SECURE_USB_RECHECK_CMD = b"\xB4"
        SECURE_USB_DECRYPT_CMD = b"\xB5"
        NFB_BL_FEATURE_CHECK_CMD = b"\xB6"  # deprecated
        NOR_BL_FEATURE_CHECK_CMD = b"\xB7"  # deprecated

        SF_WRITE_IMAGE_CMD = b"\xB8"  # deprecated

        # Android S-USBDL
        SECURE_USB_IMG_INFO_CHECK_CMD = b"\xB9"
        SECURE_USB_WRITE = b"\xBA"
        SECURE_USB_ROM_INFO_UPDATE_CMD = b"\xBB"
        SECURE_USB_GET_CUST_NAME_CMD = b"\xBC"
        SECURE_USB_CHECK_BYPASS_CMD = b"\xBE"
        SECURE_USB_GET_BL_SEC_VER_CMD = b"\xBF"
        # Android S-USBDL

        VERIFY_IMG_CHKSUM_CMD = b"\xBD"

        GET_BATTERY_VOLTAGE_CMD = b"\xD0"
        POST_PROCESS = b"\xD1"
        SPEED_CMD = b"\xD2"
        MEM_CMD = b"\xD3"
        FORMAT_CMD = b"\xD4"
        WRITE_CMD = b"\xD5"
        READ_CMD = b"\xD6"
        WRITE_REG16_CMD = b"\xD7"
        READ_REG16_CMD = b"\xD8"
        FINISH_CMD = b"\xD9"
        GET_DSP_VER_CMD = b"\xDA"
        ENABLE_WATCHDOG_CMD = b"\xDB"
        NFB_WRITE_BLOADER_CMD = b"\xDC"  # deprecated
        NAND_IMAGE_LIST_CMD = b"\xDD"
        NFB_WRITE_IMAGE_CMD = b"\xDE"
        NAND_READPAGE_CMD = b"\xDF"
        CHK_PC_SEC_INFO_CMD = b"\xE0"
        UPDATE_FLASHTOOL_CFG_CMD = b"\xE1"
        CUST_PARA_GET_INFO_CMD = b"\xE2"  # deprecated
        CUST_PARA_READ_CMD = b"\xE3"  # deprecated
        CUST_PARA_WRITE_CMD = b"\xE4"  # deprecated
        SEC_RO_GET_INFO_CMD = b"\xE5"  # deprecated
        SEC_RO_READ_CMD = b"\xE6"  # deprecated
        SEC_RO_WRITE_CMD = b"\xE7"  # deprecated
        ENABLE_DRAM = b"\xE8"
        OTP_CHECKDEVICE_CMD = b"\xE9"
        OTP_GETSIZE_CMD = b"\xEA"
        OTP_READ_CMD = b"\xEB"
        OTP_PROGRAM_CMD = b"\xEC"
        OTP_LOCK_CMD = b"\xED"
        OTP_LOCK_CHECKSTATUS_CMD = b"\xEE"
        GET_PROJECT_ID_CMD = b"\xEF"
        GET_FAT_INFO_CMD = b"\xF0"  # deprecated
        FDM_MOUNTDEVICE_CMD = b"\xF1"
        FDM_SHUTDOWN_CMD = b"\xF2"
        FDM_READSECTORS_CMD = b"\xF3"
        FDM_WRITESECTORS_CMD = b"\xF4"
        FDM_MEDIACHANGED_CMD = b"\xF5"
        FDM_DISCARDSECTORS_CMD = b"\xF6"
        FDM_GETDISKGEOMETRY_CMD = b"\xF7"
        FDM_LOWLEVELFORMAT_CMD = b"\xF8"
        FDM_NONBLOCKWRITESECTORS_CMD = b"\xF9"
        FDM_RECOVERABLEWRITESECTORS_CMD = b"\xFA"
        FDM_RESUMESECTORSTATES = b"\xFB"
        NAND_EXTRACT_NFB_CMD = b"\xFC"  # deprecated
        NAND_INJECT_NFB_CMD = b"\xFD"  # deprecated

        MEMORY_TEST_CMD = b"\xFE"
        ENTER_RELAY_MODE_CMD = b"\xFF"

    def __init__(self, mtk, daconfig, loglevel=logging.INFO):
        self.__logger = self.__logger
        self.emmc = None
        self.nand = None
        self.nor = None
        self.sdc = None
        self.flashconfig = None
        self.mtk = mtk
        self.blver = 1
        self.daconfig = daconfig
        self.eh = ErrorHandler()
        self.config = self.mtk.config
        self.info = self.__logger.info
        self.debug = self.__logger.debug
        self.error = self.__logger.error
        self.warning = self.__logger.warning
        self.usbwrite = self.mtk.port.usbwrite
        self.usbread = self.mtk.port.usbread
        self.echo = self.mtk.port.echo
        self.rbyte = self.mtk.port.rbyte
        self.rdword = self.mtk.port.rdword
        self.rword = self.mtk.port.rword
        self.sectorsize = self.daconfig.pagesize
        self.totalsectors = self.daconfig.flashsize
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

    def read_pmt(self):  # A5
        class GptEntries:
            partentries = []

            def __init__(self, sectorsize, totalsectors):
                self.sectorsize = sectorsize
                self.totalsectors = totalsectors

            def print(self):
                print("\nGPT Table:\n-------------")
                for partition in self.partentries:
                    print("{:20} Offset 0x{:016x}, Length 0x{:016x}, Flags 0x{:08x}, UUID {}, Type {}".format(
                        partition.name + ":", partition.sector * self.sectorsize, partition.sectors * self.sectorsize,
                        partition.flags, partition.unique, partition.type))
                print("\nTotal disk size:0x{:016x}, sectors:0x{:016x}".format(self.totalsectors * self.sectorsize,
                                                                              self.totalsectors))

        gpt = GptEntries(self.sectorsize, self.totalsectors)

        class PartitionLegacy:
            type = 0
            unique = b""
            sector = 0
            sectors = 0
            flags = 0
            name = ""

        if self.usbwrite(self.Cmd.SDMMC_READ_PMT_CMD):
            ack = unpack(">B", self.usbread(1))[0]
            if ack == 0x5a:
                datalength = unpack(">I", self.usbread(4))[0]
                if self.usbwrite(self.Rsp.ACK):
                    partdata = self.usbread(datalength, 0x200)
                    if self.usbwrite(self.Rsp.ACK):
                        if partdata[0x48] == 0xFF:
                            for pos in range(0, datalength, 0x60):
                                partname = partdata[pos:pos + 0x40].rstrip(b"\x00").decode('utf-8')
                                size = unpack("<Q", partdata[pos + 0x40:pos + 0x48])[0]
                                mask_flags = unpack("<Q", partdata[pos + 0x48:pos + 0x50])[0]
                                offset = unpack("<Q", partdata[pos + 0x50:pos + 0x58])[0]
                                p = PartitionLegacy()
                                p.name = partname
                                p.type = 1
                                p.sector = offset // self.daconfig.pagesize
                                p.sectors = size // self.daconfig.pagesize
                                p.flags = mask_flags
                                p.unique = b""
                                gpt.partentries.append(p)
                        else:
                            mask_flags = unpack("<Q", partdata[0x48:0x4C])[0]
                            if 0xA > mask_flags > 0:
                                # 64Bit
                                for pos in range(0, datalength, 0x58):
                                    partname = partdata[pos:pos + 0x40].rstrip(b"\x00").decode('utf-8')
                                    size = unpack("<Q", partdata[pos + 0x40:pos + 0x48])[0]
                                    offset = unpack("<Q", partdata[pos + 0x48:pos + 0x50])[0]
                                    mask_flags = unpack("<Q", partdata[pos + 0x50:pos + 0x58])[0]
                                    p = PartitionLegacy()
                                    p.name = partname
                                    p.type = 1
                                    p.sector = offset // self.daconfig.pagesize
                                    p.sectors = size // self.daconfig.pagesize
                                    p.flags = mask_flags
                                    p.unique = b""
                                    gpt.partentries.append(p)
                            else:
                                # 32Bit
                                for pos in range(0, datalength, 0x4C):
                                    partname = partdata[pos:pos + 0x40]
                                    size = unpack("<Q", partdata[pos + 0x40:pos + 0x44])[0]
                                    offset = unpack("<Q", partdata[pos + 0x44:pos + 0x48])[0]
                                    mask_flags = unpack("<Q", partdata[pos + 0x48:pos + 0x4C])[0]
                                    p = PartitionLegacy()
                                    p.name = partname
                                    p.type = 1
                                    p.sector = offset // self.daconfig.pagesize
                                    p.sectors = size // self.daconfig.pagesize
                                    p.flags = mask_flags
                                    p.unique = b""
                                    gpt.partentries.append(p)
                        return partdata, gpt
        return b"", []

    def get_part_info(self):
        res = self.mtk.port.mtk_cmd(self.Cmd.SDMMC_READ_PMT_CMD, 1 + 4)  # 0xA5
        value, length = unpack(">BI", res)
        self.usbwrite(self.Rsp.ACK)
        data = self.usbread(length)
        self.usbwrite(self.Rsp.ACK)
        return data

    def sdmmc_switch_partition(self, partition):
        if self.usbwrite(self.Cmd.SDMMC_SWITCH_PART_CMD):
            ack = self.usbread(1)
            if ack == self.Rsp.ACK:
                self.usbwrite(pack(">B", partition))
                res = self.usbread(1)
                if res < 0:
                    return False
                else:
                    return True
        return False

    def check_security(self):
        cmd = self.Cmd.CHK_PC_SEC_INFO_CMD + pack(">I", 0)  # E0
        ack = self.mtk.port.mtk_cmd(cmd, 1)
        if ack == self.Rsp.ACK:
            return True
        return False

    def recheck(self):  # If Preloader is needed
        sec_info_len = 0
        cmd = self.Cmd.SECURE_USB_RECHECK_CMD + pack(">I", sec_info_len)  # B4
        status = unpack(">I", self.mtk.port.mtk_cmd(cmd, 1))[0]
        if status == 0x1799:
            return False  # S-USBDL disabled
        return True

    def set_stage2_config(self, hwcode):
        # m_nor_chip_select[0]="CS_0"(0x00), m_nor_chip_select[1]="CS_WITH_DECODER"(0x08)
        m_nor_chip = 0x08
        self.usbwrite(pack(">H", m_nor_chip))
        m_nor_chip_select = 0x00
        self.usbwrite(pack("B", m_nor_chip_select))
        m_nand_acccon = 0x7007FFFF
        self.usbwrite(pack(">I", m_nand_acccon))
        self.config.bmtsettings(self.config.hwcode)
        self.usbwrite(pack("B", self.config.bmtflag))
        self.usbwrite(pack(">I", self.config.bmtpartsize))
        # self.usbwrite(pack(">I", bmtblockcount))
        # unsigned char force_charge=0x02; //Setting in tool: 0x02=Auto, 0x01=On
        force_charge = 0x02
        self.usbwrite(pack("B", force_charge))
        resetkeys = 0x01  # default
        if hwcode == 0x6583:
            resetkeys = 0
        self.usbwrite(pack("B", resetkeys))
        # EXT_CLOCK: ext_clock(0x02)="EXT_26M".
        extclock = 0x02
        self.usbwrite(pack("B", extclock))
        msdc_boot_ch = 0
        self.usbwrite(pack("B", msdc_boot_ch))
        toread = 4
        if hwcode == 0x6592:
            is_gpt_solution = 0
            self.usbwrite(pack(">I", is_gpt_solution))
            toread = (6 * 4)
        elif hwcode == 0x8163:
            slc_percent = 0x20000
            self.usbwrite(pack(">I", slc_percent))
        elif hwcode == 0x6580:
            slc_percent = 0x1
            self.usbwrite(pack(">I", slc_percent))
            unk = b"\x46\x46\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x00\x00\x00"
            self.usbwrite(unk)
        elif hwcode in [0x6583, 0x6589]:
            forcedram = 0
            if hwcode == 0x6583:
                forcedram = 0
            elif hwcode == 0x6589:
                forcedram = 1
            self.usbwrite(pack(">I", forcedram))
        elif hwcode == 0x8127:
            skipdl = 0
            self.usbwrite(pack(">I", skipdl))
        elif hwcode == 0x6582:
            newcombo = 0
            self.usbwrite(pack(">I", newcombo))
        time.sleep(0.350)
        buffer = self.usbread(toread)
        if toread == 4 and buffer == pack(">I", 0xBC3):
            buffer += self.usbread(4)
            draminfo = self.usbread(16)
            draminfo_rev = draminfo[:4][::-1] + draminfo[4:8][::-1] + draminfo[8:12][::-1] + draminfo[12:16][::-1]
            draminfo_rev = draminfo_rev[:9]
            draminfo = draminfo[:9]
            self.info("DRAM config needed for : " + hexlify(draminfo).decode('utf-8'))
            if self.daconfig.preloader is None:
                found = False
                for root, dirs, files in os.walk(os.path.join('Loader', 'Preloader')):
                    for file in files:
                        with open(os.path.join(root, file), "rb") as rf:
                            data = rf.read()
                            if draminfo in data or draminfo_rev in data:
                                self.daconfig.preloader = os.path.join(root, file)
                                print("Detected preloader: " + self.daconfig.preloader)
                                found = True
                                break
                    if found:
                        break
            if self.usbread(4) == pack(">I", 0xBC4):  # Nand_Status
                nand_id_count = unpack(">H", self.usbread(2))[0]
                nand_ids = []
                for i in range(0, nand_id_count):
                    nand_ids.append(unpack(">H", self.usbread(2))[0])
                if self.daconfig.preloader is not None:
                    with open(self.daconfig.preloader, 'rb') as rf:
                        data = rf.read()
                        dramdata = data[data.rfind(b"MTK_BIN"):][0xC:][:-0x128]
                    self.usbwrite(self.Cmd.ENABLE_DRAM)  # E8
                    if self.config.hwcode == 0x6580:
                        val = 0x15
                    else:
                        val = 0x14
                    self.usbwrite(pack(">I", val))
                    if self.usbread(1) == self.Rsp.ACK:
                        info = unpack(">I", self.usbread(4))[0]  # 0x000000BC
                        self.debug("Info: " + hex(info))
                        self.usbwrite(self.Rsp.ACK)
                        dramlength = len(dramdata)
                        self.usbwrite(pack(">I", dramlength))
                        for pos in range(0, len(dramdata), 64):
                            self.usbwrite(dramdata[pos:pos + 64])
                        status = unpack(">H", self.usbread(2))[0]  # 0x440C
                        self.debug("Status: %04X" % status)
                        self.usbwrite(self.Rsp.ACK)
                        self.usbwrite(pack(">I", 0x80000001))  # Send DRAM config
                        m_ext_ram_ret = unpack(">I", self.usbread(4))[0]  # 0x00000000 S_DONE
                        self.debug(f"M_EXT_RAM_RET : {m_ext_ram_ret}")
                        m_ext_ram_type = self.usbread(1)[0]  # 0x02 HW_RAM_DRAM
                        self.debug(f"M_EXT_RAM_TYPE : {m_ext_ram_type}")
                        m_ext_ram_chip_select = self.usbread(1)[0]  # 0x00 CS_0
                        self.debug(f"M_EXT_RAM_CHIP_SELECT : {m_ext_ram_chip_select}")
                        m_ext_ram_size = unpack(">Q", self.usbread(8))  # 0x80000000
                        self.debug(f"M_EXT_RAM_SIZE : {m_ext_ram_size}")
                else:
                    self.error("Preloader needed due to dram config.")
                    self.mtk.port.close()
                    sys.exit(0)
        return buffer

    def read_flash_info(self):
        data = self.usbread(0x1C)
        self.nor = read_object(data, norinfo)
        data = self.usbread(0x11)
        self.nand = read_object(data, nandinfo64)
        nandcount = self.nand["m_nand_flash_id_count"]
        if nandcount == 0:
            self.nand = read_object(data, nandinfo32)
            nandcount = self.nand["m_nand_flash_id_count"]
            nc = data[-4:] + self.usbread(nandcount * 2 - 4)
        else:
            nc = self.usbread(nandcount * 2)
        m_nand_dev_code = unpack(">" + str(nandcount) + "H", nc)
        self.nand["m_nand_flash_dev_code"] = m_nand_dev_code
        ni2 = read_object(self.usbread(9), nandinfo2)
        for ni in ni2:
            self.nand[ni] = ni2[ni]
        self.emmc = read_object(self.usbread(0x5C), emmcinfo)
        self.sdc = read_object(self.usbread(0x1C), sdcinfo)
        self.flashconfig = read_object(self.usbread(0x26), configinfo)
        pi = read_object(self.usbread(0xA), passinfo)
        if pi["ack"] == 0x5A:
            return True
        return False

    def upload(self):
        if self.daconfig.da is None:
            self.error("No valid da loader found... aborting.")
            return False
        loader = self.daconfig.loader
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
                    if self.mtk.preloader.jump_da(address):
                        sync = self.usbread(1)
                        if sync != b"\xC0":
                            self.error("Error on DA sync")
                            return False
                    else:
                        return False
                else:
                    return False
                nandinfo = unpack(">I", self.usbread(4))[0]
                self.debug("NAND_INFO: " + hex(nandinfo))
                ids = unpack(">H", self.usbread(2))[0]
                nandids = []
                for i in range(0, ids):
                    tmp = unpack(">H", self.usbread(2))[0]
                    nandids.append(tmp)

                emmcinfolegacy = unpack(">I", self.usbread(4))[0]
                self.debug("EMMC_INFO: " + hex(emmcinfolegacy))
                emmcids = []
                for i in range(0, 4):
                    tmp = unpack(">I", self.usbread(4))[0]
                    emmcids.append(tmp)

                if nandids[0] != 0:
                    self.daconfig.flashtype = "nand"
                elif emmcids[0] != 0:
                    self.daconfig.flashtype = "emmc"
                else:
                    self.daconfig.flashtype = "nor"

                self.usbwrite(self.Rsp.ACK)
                ackval = self.usbread(3)
                self.debug("ACK: " + hexlify(ackval).decode('utf-8'))

                self.usbwrite(self.Cmd.GET_PROJECT_ID_CMD)
                self.usbwrite(pack("B", self.config.blver))

                self.set_stage2_config(self.config.hwcode)
                self.info("Uploading stage 2...")
                # stage 2
                if self.brom_send(self.daconfig.da, bootldr, self.config.blver + 2):
                    if self.read_flash_info():
                        if self.daconfig.flashtype == "nand":
                            self.daconfig.flashsize = self.nand["m_nand_flash_size"]
                        elif self.daconfig.flashtype == "emmc":
                            self.daconfig.flashsize = self.emmc["m_emmc_ua_size"]
                            if self.daconfig.flashsize == 0:
                                self.daconfig.flashsize = self.sdc["m_sdmmc_ua_size"]
                        elif self.daconfig.flashtype == "nor":
                            self.daconfig.flashsize = self.nor["m_nor_flash_size"]
                        return True
                return False

    def upload_da(self):
        self.config.blver = self.mtk.preloader.get_blver()
        self.info("Uploading da...")
        if self.upload():
            if self.emmc == "nor":
                flashinfo = self.nor
            elif self.emmc == "nand":
                flashinfo = self.nand
            else:
                fo = self.emmc
                fo2 = self.sdc
                flashinfo = {}
                for v in fo:
                    flashinfo[v] = fo[v]
                for v in fo2:
                    flashinfo[v] = fo2[v]
            self.printinfo(flashinfo)
            self.printinfo(self.flashconfig)
            return True
        return False

    def printinfo(self, fi):
        for info in fi:
            value = fi[info]
            if info != "raw_data":
                subtype = type(value)
                if subtype is bytes:
                    self.info(info + ": " + hexlify(value).decode('utf-8'))
                elif subtype is int:
                    self.info(info + ": " + hex(value))

    def close(self):
        self.finish(0x0)  # DISCONNECT_USB_AND_RELEASE_POWERKEY
        self.mtk.port.close()

    def brom_send(self, dasetup, da, stage, packetsize=0x1000):
        offset = dasetup[stage]["m_buf"]
        size = dasetup[stage]["m_len"]
        address = dasetup[stage]["m_start_addr"]
        da.seek(offset)
        dadata = da.read(size)
        self.usbwrite(pack(">I", address))
        self.usbwrite(pack(">I", size))
        self.usbwrite(pack(">I", packetsize))
        buffer = self.usbread(1)
        if buffer == self.Rsp.ACK:
            for pos in range(0, size, packetsize):
                self.usbwrite(dadata[pos:pos + packetsize])
                buffer = self.usbread(1)
                if buffer != self.Rsp.ACK:
                    self.error(
                        f"Error on sending brom stage {stage} addr {hex(pos)}: " + hexlify(buffer).decode('utf-8'))
                    break
            time.sleep(0.5)
            self.usbwrite(self.Rsp.ACK)
            buffer = self.usbread(1)
            if buffer == self.Rsp.ACK:
                return True
        else:
            self.error(f"Error on sending brom stage {stage} : " + hexlify(buffer).decode('utf-8'))
        return False

    def check_usb_cmd(self):
        if self.usbwrite(self.Cmd.USB_CHECK_STATUS):  # 72
            res = self.usbread(2)
            if len(res) > 1:
                if res[0] is self.Rsp.ACK[0]:
                    return True
        return False

    def sdmmc_switch_part(self, partition=0x8):
        self.usbwrite(self.Cmd.SDMMC_SWITCH_PART_CMD)  # 60
        ack = self.usbread(1)
        if ack == self.Rsp.ACK:
            # partition = 0x8  # EMMC_Part_User = 0x8, sonst 0x0
            self.usbwrite(pack("B", partition))
            ack = self.usbread(1)
            if ack == self.Rsp.ACK:
                return True
        return False

    def finish(self, value):
        self.usbwrite(self.Cmd.FINISH_CMD)  # D9
        ack = self.usbread(1)[0]
        if ack is self.Rsp.ACK:
            self.usbwrite(pack(">I", value))
            ack = self.usbread(1)[0]
            if ack is self.Rsp.ACK:
                return True
        return False

    def sdmmc_write_data(self, addr, length, filename, parttype=None, display=True):
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

        if filename != "":
            with open(filename, "rb") as rf:
                if display:
                    print_progress(0, 100, prefix='Progress:', suffix='Complete', bar_length=50)
                self.usbwrite(self.Cmd.SDMMC_WRITE_DATA_CMD)
                self.usbwrite(pack(">B", storage))
                self.usbwrite(pack(">B", parttype))
                self.usbwrite(pack(">Q", addr))
                self.usbwrite(pack(">Q", length))
                self.usbwrite(pack(">I", 0x100000))
                if self.usbread(1) != self.Rsp.ACK:
                    self.error("Couldn't send sdmmc_write_data header")
                    return False
                offset = 0
                old = 0
                while offset < length:
                    self.usbwrite(self.Rsp.ACK)
                    count = min(0x100000, length - offset)
                    data = bytearray(rf.read(count))
                    self.usbwrite(data)
                    chksum = sum(data) & 0xFFFF
                    self.usbwrite(pack(">H", chksum))
                    if self.usbread(1) != self.Rsp.CONT_CHAR:
                        self.error("Data ack failed for sdmmc_write_data")
                        return False
                    if display:
                        prog = offset / length * 100
                        if round(prog, 1) > old:
                            print_progress(prog, 100, prefix='Progress:',
                                           suffix='Complete, Sector:' + hex(offset), bar_length=50)
                            old = round(prog, 1)
                    offset += count
                if display:
                    print_progress(100, 100, prefix='Progress:', suffix='Complete', bar_length=50)
                return True

    def sdmmc_write_image(self, addr, length, filename, display=True):
        if filename != "":
            with open(filename, "rb") as rf:
                if self.daconfig.flashtype == "emmc":
                    self.usbwrite(self.Cmd.SDMMC_WRITE_IMAGE_CMD)  # 61
                    self.usbwrite(b"\x00")  # checksum level 0
                    self.usbwrite(b"\x08")  # EMMC_PART_USER
                    self.usbwrite(pack(">Q", addr))
                    self.usbwrite(pack(">Q", length))
                    self.usbwrite(b"\x08")  # index 8
                    self.usbwrite(b"\x03")
                    packetsize = unpack(">I", self.usbread(4))[0]
                    ack = unpack(">B", self.usbread(1))[0]
                    if ack == self.Rsp.ACK[0]:
                        self.usbwrite(self.Rsp.ACK)
                if display:
                    print_progress(0, 100, prefix='Progress:', suffix='Complete', bar_length=50)
                old = 0
                checksum = 0
                bytestowrite = length
                while bytestowrite > 0:
                    size = min(bytestowrite, packetsize)
                    for i in range(0, size, 0x400):
                        data = bytearray(rf.read(size))
                        pos = length - bytestowrite
                        if display:
                            prog = pos / length * 100
                            if round(prog, 1) > old:
                                print_progress(prog, 100, prefix='Progress:',
                                               suffix='Complete, Sector:' + hex(pos), bar_length=50)
                                old = round(prog, 1)
                        if self.usbwrite(data):
                            bytestowrite -= size
                            if bytestowrite == 0:
                                checksum = 0
                                for val in data:
                                    checksum += val
                                checksum = checksum & 0xFFFF
                                self.usbwrite(pack(">H", checksum))
                            if self.usbread(1) == b"\x69":
                                if bytestowrite == 0:
                                    self.usbwrite(pack(">H", checksum))
                                if self.usbread(1) == self.Rsp.ACK:
                                    return True
                                else:
                                    self.usbwrite(self.Rsp.ACK)
                return True
        return True

    def writeflash(self, addr, length, filename, partitionname, parttype=None, display=True):
        return self.sdmmc_write_data(addr=addr, length=length, filename=filename, parttype=parttype, display=display)

    def formatflash(self, addr, length, parttype=None, display=True):
        return False

    def readflash(self, addr, length, filename, parttype=None, display=True):
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
        self.check_usb_cmd()
        packetsize = 0x0
        if self.daconfig.flashtype == "emmc":
            self.sdmmc_switch_part(parttype)
            packetsize = 0x100000
            self.usbwrite(self.Cmd.READ_CMD)  # D6
            self.usbwrite(b"\x0C")  # Host:Linux, 0x0B=Windows
            self.usbwrite(b"\x02")  # Storage-Type: EMMC
            self.usbwrite(pack(">Q", addr))
            self.usbwrite(pack(">Q", length))
            self.usbwrite(pack(">I", packetsize))
            ack = self.usbread(1)[0]
            if ack is not self.Rsp.ACK[0]:
                self.error(f"Error on sending read command, response: {hex(ack)}")
                exit(1)
            self.daconfig.readsize = self.daconfig.flashsize
        elif self.daconfig.flashtype == "nand":
            self.usbwrite(self.Cmd.NAND_READPAGE_CMD)  # DF
            self.usbwrite(b"\x0C")  # Host:Linux, 0x0B=Windows
            self.usbwrite(b"\x00")  # Storage-Type: NUTL_READ_PAGE_SPARE
            self.usbwrite(b"\x01")  # Addr-Type: NUTL_ADDR_LOGICAL
            self.usbwrite(pack(">I", addr))
            self.usbwrite(pack(">I", length))
            self.usbwrite(pack(">I", 0))
            ack = self.usbread(1)[0]
            if ack is not self.Rsp.ACK:
                self.error(f"Error on sending read command, response: {hex(ack)}")
                exit(1)
            self.daconfig.pagesize = unpack(">I", self.usbread(4))[0]
            self.daconfig.sparesize = unpack(">I", self.usbread(4))[0]
            packetsize = unpack(">I", self.usbread(4))[0]
            pagestoread = 1
            self.usbwrite(pack(">I", pagestoread))
            self.usbread(4)
            self.daconfig.readsize = self.daconfig.flashsize // self.daconfig.pagesize * (
                    self.daconfig.pagesize + self.daconfig.sparesize)
        if display:
            print_progress(0, 100, prefix='Progress:', suffix='Complete', bar_length=50)
        old = 0

        if filename != "":
            with open(filename, "wb") as wf:
                bytestoread = length
                while bytestoread > 0:
                    size = bytestoread
                    if bytestoread > packetsize:
                        size = packetsize
                    data = self.usbread(size, 0x400)
                    wf.write(data)
                    bytestoread -= size
                    checksum = unpack(">H", self.usbread(2))[0]
                    self.debug("Checksum: %04X" % checksum)
                    self.usbwrite(self.Rsp.ACK)
                    if display:
                        prog = (length - bytestoread) / length * 100
                        if round(prog, 1) > old:
                            print_progress(prog, 100, prefix='Progress:',
                                           suffix='Complete, Sector:' + hex(length - bytestoread), bar_length=50)
                            old = round(prog, 1)
                return True
        else:
            buffer = bytearray()
            bytestoread = length
            while bytestoread > 0:
                size = bytestoread
                if bytestoread > packetsize:
                    size = packetsize
                buffer.extend(self.usbread(size, 0x400))
                bytestoread -= size
                checksum = unpack(">H", self.usbread(2))[0]
                self.debug("Checksum: %04X" % checksum)
                self.usbwrite(self.Rsp.ACK)
                if display:
                    prog = (length - bytestoread) / length * 100
                    if round(prog, 1) > old:
                        print_progress(prog, 100, prefix='Progress:', suffix='Complete', bar_length=50)
                        old = round(prog, 1)
            return buffer
