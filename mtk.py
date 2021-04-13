#!/usr/bin/env python3
# MTK Flash Client (c) B.Kerler 2018-2021.
# Licensed under MIT License
"""
Usage:
    mtk.py -h | --help
    mtk.py [--vid=vid] [--pid=pid]
    mtk.py [--loader=filename]
    mtk.py [--debugmode]
    mtk.py [--gpt-num-part-entries=number] [--gpt-part-entry-size=number] [--gpt-part-entry-start-lba=number]
    mtk.py [--sectorsize=bytes]
    mtk.py printgpt [--memory=memtype] [--lun=lun] [--preloader=filename] [--loader=filename] [--debugmode] [--vid=vid] [--pid=pid]
    mtk.py gpt <filename> [--memory=memtype] [--lun=lun] [--preloader=filename] [--loader=filename] [--debugmode] [--vid=vid] [--pid=pid]
    mtk.py r <partitionname> <filename> [--parttype=parttype] [--memory=memtype] [--lun=lun] [--preloader=filename] [--payload=filename] [--loader=filename] [--debugmode] [--vid=vid] [--pid=pid] [--var1=var1]
    mtk.py rl <directory> [--memory=memtype] [--parttype=parttype] [--lun=lun] [--skip=partnames] [--preloader=filename] [--payload=filename] [--loader=filename] [--debugmode] [--vid=vid] [--pid=pid] [--var1=var1]
    mtk.py rf <filename> [--memory=memtype] [--parttype=parttype] [--lun=lun] [--preloader=filename] [--loader=filename] [--payload=filename] [--debugmode] [--vid=vid] [--pid=pid] [--var1=var1]
    mtk.py rs <start_sector> <sectors> <filename> [--parttype=parttype] [--lun=lun] [--preloader=filename] [--loader=filename] [--payload=filename] [--debugmode] [--vid=vid] [--pid=pid] [--var1=var1]
    mtk.py w <partitionname> <filename> [--parttype=parttype] [--memory=memtype] [--lun=lun] [--preloader=filename] [--loader=filename] [--payload=filename] [--debugmode] [--vid=vid] [--pid=pid] [--var1=var1]
    mtk.py e <partitionname> [--parttype=parttype] [--memory=memtype] [--lun=lun] [--preloader=filename] [--loader=filename] [--payload=filename] [--debugmode] [--vid=vid] [--pid=pid] [--var1=var1]
    mtk.py footer <filename> [--memory=memtype] [--lun=lun] [--preloader=filename] [--loader=filename] [--payload=filename] [--debugmode] [--vid=vid] [--pid=pid] [--var1=var1]
    mtk.py reset [--debugmode] [--vid=vid] [--pid=pid]
    mtk.py dumpbrom [--filename=filename] [--ptype=ptype] [--crash] [--skipwdt] [--wdt=wdt] [--var1=var1] [--da_addr=addr] [--brom_addr=addr] [--uartaddr=addr] [--debugmode] [--vid=vid] [--pid=pid] [--interface=interface] [--socid]
    mtk.py payload [--payload=filename] [--ptype=ptype] [--crash] [--var1=var1] [--skipwdt] [--wdt=wdt] [--uartaddr=addr] [--da_addr=addr] [--brom_addr=addr] [--debugmode] [--vid=vid] [--pid=pid] [--interface=interface] [--socid]
    mtk.py crash [--mode=mode] [--debugmode] [--skipwdt] [--vid=vid] [--pid=pid] [--socid]
    mtk.py brute [--var1=var1] [--socid]
    mtk.py gettargetconfig [--debugmode] [--vid=vid] [--pid=pid] [--socid]
    mtk.py peek <offset> <length> [--filename=filename] [--preloader=preloader]
    mtk.py stage [--stage2=filename] [--stage2addr=addr] [--stage1=filename] [--verifystage2] [--crash] [--socid]
    mtk.py plstage [--filename=filename] [--socid]

Description:
    printgpt            # Print GPT Table information
    gpt                 # Save gpt table to given directory
    r                   # Read flash to filename
    rl                  # Read all partitions from flash to a directory
    rf                  # Read whole flash to file
    rs                  # Read sectors starting at start_sector to filename
    w                   # Write flash to filename
    footer              # Read crypto footer from flash
    reset               # Send mtk reset command
    brute               # Bruteforce the kamakiri var1
    dumpbrom            # Try to dump the bootrom
    crash               # Try to crash the preloader
    gettargetconfig     # Get target config (sbc, daa, etc.)
    payload             # Run a specific kamakiri / da payload, if no filename is given, generic patcher is used
    stage               # Run stage2 payload via boot rom mode (kamakiri)
    plstage             # Run stage2 payload via preloader mode (send_da)

Options:
    --loader=filename                  Use specific DA loader, disable autodetection
    --vid=vid                          Set usb vendor id used for MTK Preloader
    --pid=pid                          Set usb product id used for MTK Preloader
    --sectorsize=bytes                 Set default sector size [default: 0x200]
    --debugmode                        Enable verbose mode
    --gpt-num-part-entries=number      Set GPT entry count [default: 0]
    --gpt-part-entry-size=number       Set GPT entry size [default: 0]
    --gpt-part-entry-start-lba=number  Set GPT entry start lba sector [default: 0]
    --skip=partnames                   Skip reading partition with names "partname1,partname2,etc."
    --wdt=wdt                          Set a specific watchdog addr
    --mode=mode                        Set a crash mode (0=dasend1,1=dasend2,2=daread)
    --var1=var1                        Set kamakiri specific var1 value
    --uart_addr=addr                   Set payload uart_addr value
    --da_addr=addr                     Set a specific da payload addr
    --brom_addr=addr                   Set a specific brom payload addr
    --ptype=ptype                      Set the payload type ("amonet","kamakiri",kamakiri/da used by default)
    --uartaddr=addr                    Set the payload uart addr
    --preloader=filename               Set the preloader filename for dram config
    --skipwdt                          Skip wdt init
    --verifystage2                     Verify if stage2 data has been written correctly
    --parttype=parttype                Partition type (user,boot1,boot2,gp1,gp2,gp3,gp4,rpmb)
    --filename=filename                Optional filename
    --crash                            Enforce crash if device is in pl mode to enter brom mode
    --socid                            Read Soc ID
"""

from docopt import docopt

from config.usb_ids import default_ids
from Library.pltools import PLTools
from Library.mtk_preloader import Preloader
from Library.mtk_daloader import DAloader
from Library.Port import Port
from Library.utils import *
from config.brom_config import Mtk_Config

import time
from binascii import hexlify


def split_by_n(seq, unit_count):
    """A generator to divide a sequence into chunks of n units."""
    while seq:
        yield seq[:unit_count]
        seq = seq[unit_count:]


class Mtk(metaclass=LogBase):
    def __init__(self, args, loader, loglevel=logging.INFO, vid=-1, pid=-1, interface=0):
        self.__logger = self.__logger
        self.config = Mtk_Config(self, loglevel)
        self.args = args
        self.info = self.__logger.info
        self.error = self.__logger.error
        self.warning = self.__logger.warning
        if loglevel == logging.DEBUG:
            logfilename = os.path.join("logs", "log.txt")
            if os.path.exists(logfilename):
                os.remove(logfilename)
            fh = logging.FileHandler(logfilename)
            self.__logger.addHandler(fh)
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger.setLevel(logging.INFO)
        da_address = self.args["--da_addr"]
        if da_address is not None:
            self.config.chipconfig.da_payload_addr = getint(da_address)

        brom_address = self.args["--brom_addr"]
        if brom_address is not None:
            self.config.chipconfig.brom_payload_addr = getint(brom_address)

        watchdog_address = self.args["--wdt"]
        if watchdog_address is not None:
            self.config.chipconfig.watchdog = getint(watchdog_address)

        uart_address = self.args["--uartaddr"]
        if uart_address is not None:
            self.config.chipconfig.uart = getint(uart_address)

        var1 = self.args["--var1"]
        if var1 is not None:
            self.config.chipconfig.var1 = getint(var1)

        preloader = self.args["--preloader"]

        if vid != -1 and pid != -1:
            if interface == -1:
                for dev in default_ids:
                    if dev[0] == vid and dev[1] == pid:
                        interface = dev[2]
                        break
            portconfig = [[vid, pid, interface]]
        else:
            portconfig = default_ids
        self.port = Port(self, portconfig, self.__logger.level)
        self.preloader = Preloader(self, self.__logger.level)
        self.daloader = DAloader(self, loader, preloader, self.__logger.level)


class Main(metaclass=LogBase):
    def __init__(self):
        self.__logger = self.__logger
        self.info = self.__logger.info
        self.debug = self.__logger.debug
        self.error = self.__logger.error
        self.warning = self.__logger.warning
        self.args = docopt(__doc__, version='EDL 2.1')
        if not os.path.exists("logs"):
            os.mkdir("logs")

    def close(self):
        sys.exit(0)

    def crasher(self, rmtk, enforcecrash, readsocid=False, display=True, mode=None):
        plt = PLTools(rmtk, self.__logger.level)
        if enforcecrash or not (rmtk.port.cdc.vid == 0xE8D and rmtk.port.cdc.pid == 0x0003):
            self.info("We're not in bootrom, trying to crash da...")
            if mode is None:
                for crashmode in range(0, 3):
                    try:
                        plt.crash(crashmode)
                    except Exception as err:
                        self.__logger.debug(str(err))
                        pass
                    rmtk = Mtk(loader=self.args["--loader"], loglevel=self.__logger.level, vid=0xE8D, pid=0x0003,
                               args=self.args, interface=1)
                    rmtk.preloader.display = display
                    if rmtk.preloader.init(args=self.args, readsocid=readsocid, maxtries=20):
                        break
            else:
                try:
                    plt.crash(mode)
                except Exception as err:
                    self.__logger.debug(str(err))
                    pass
                rmtk = Mtk(loader=self.args["--loader"], loglevel=self.__logger.level, vid=0xE8D, pid=0x0003,
                           interface=1, args=self.args)
                rmtk.preloader.display = display
                if rmtk.preloader.init(args=self.args, readsocid=readsocid, maxtries=20):
                    return rmtk
        return rmtk

    def run(self):
        if self.args["--vid"] is not None:
            vid = getint(self.args["--vid"])
        else:
            vid = -1
        if self.args["--pid"] is not None:
            pid = getint(self.args["--pid"])
        else:
            pid = -1
        enforcecrash = False
        readsocid = False
        if self.args["--socid"] is not None:
            readsocid = self.args["--socid"]
        if self.args["--crash"]:
            enforcecrash = True
        if self.args["--debugmode"]:
            logfilename = os.path.join("logs", "log.txt")
            if os.path.exists(logfilename):
                os.remove(logfilename)
            fh = logging.FileHandler(logfilename)
            self.__logger.addHandler(fh)
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger.setLevel(logging.INFO)
        interface = -1
        # pagesize = getint(self.args["--sectorsize"])
        mtk = Mtk(loader=self.args["--loader"], loglevel=self.__logger.level, vid=vid, pid=pid, interface=interface,
                  args=self.args)

        if self.args["dumpbrom"]:
            if mtk.preloader.init(args=self.args, readsocid=readsocid):
                rmtk = self.crasher(rmtk=mtk, readsocid=readsocid, enforcecrash=enforcecrash)
                if rmtk is None:
                    sys.exit(0)
                if rmtk.port.cdc.vid != 0xE8D and rmtk.port.cdc.pid != 0x0003:
                    self.warning("We couldn't enter preloader.")
                filename = self.args["--filename"]
                if filename is None:
                    cpu = ""
                    if rmtk.config.cpu != "":
                        cpu = "_" + rmtk.config.cpu
                    filename = "brom" + cpu + "_" + hex(rmtk.config.hwcode)[2:] + ".bin"
                plt = PLTools(rmtk, self.__logger.level)
                plt.run_dump_brom(filename, self.args["--ptype"])
                rmtk.port.close()
            self.close()
        elif self.args["brute"]:
            self.info("Kamakiri / DA Bruteforce run")

            var1 = self.args["--var1"]
            if var1 is not None:
                var1 = getint(var1)
                self.info("F:Var1:\t\t" + hex(var1))
            else:
                var1 = 0xA

            for i in range(var1, 0xFF):
                var1 = i
                self.warning("Trying var1 of %02X, please reconnect/connect device into bootrom mode" % var1)
                while True:
                    rmtk = Mtk(loader=self.args["--loader"], loglevel=self.__logger.level, vid=vid, pid=pid,
                               interface=interface,
                               args=self.args)
                    rmtk.preloader.display = False
                    if mtk.preloader.init(args=self.args, readsocid=readsocid):
                        rmtk = self.crasher(rmtk=rmtk, readsocid=readsocid, enforcecrash=enforcecrash, display=False)
                        try:
                            plt = PLTools(rmtk, self.__logger.level)
                            plt.kama.var1 = i
                            filename = self.args["--filename"]
                            if filename is None:
                                cpu = ""
                                if rmtk.config.cpu != "":
                                    cpu = "_" + rmtk.config.cpu
                                filename = "brom" + cpu + "_" + hex(rmtk.config.hwcode)[2:] + ".bin"
                            if plt.run_dump_brom(filename, "kamakiri"):
                                self.warning("Found a possible var1 of 0x%x" % var1)
                                return
                            else:
                                rmtk.port.close()
                                time.sleep(0.1)
                                del rmtk
                        except Exception as err:
                            self.debug(str(err))
                            time.sleep(0.1)
                            pass
                        break
                    else:
                        rmtk.port.close()
                        time.sleep(0.1)
                        del rmtk
            self.warning(f"Var1 of {hex(var1)} possibly failed, please wait a few seconds " +
                         "and then reconnect the mobile to bootrom mode")

            if var1 == 0xFF:
                self.error("Couldn't find the right var1 value.")
            self.close()
        elif self.args["crash"]:
            if mtk.preloader.init(args=self.args, readsocid=readsocid):
                self.crasher(rmtk=mtk, readsocid=readsocid, enforcecrash=enforcecrash, mode=getint(self.args["--mode"]))
            mtk.port.close()
            self.close()
        elif self.args["plstage"]:
            if self.args["--filename"] is None:
                filename = os.path.join("payloads", "pl.bin")
            else:
                filename = self.args["--filename"]
            if os.path.exists(filename):
                with open(filename, "rb") as rf:
                    rf.seek(0)
                    dadata = rf.read()
            if mtk.preloader.init(args=self.args, readsocid=readsocid):
                if mtk.config.chipconfig.pl_payload_addr is not None:
                    daaddr = mtk.config.chipconfig.pl_payload_addr
                else:
                    daaddr = 0x40200000  # 0x40001000
                if mtk.preloader.send_da(daaddr, len(dadata), 0x100, dadata):
                    self.info(f"Sent da to {hex(daaddr)}, length {hex(len(dadata))}")
                    if mtk.preloader.jump_da(daaddr):
                        self.info(f"Jumped to {hex(daaddr)}.")
                        # time.sleep(2)
                        # mtk = Mtk(loader=args["--loader"], loglevel=self.__logger.level, vid=vid, pid=pid,
                        # interface=interface,
                        # args=args)
                        ack = unpack(">I", mtk.port.usbread(4))[0]
                        if ack == 0xB1B2B3B4:
                            self.info("Successfully loaded stage2")
                            """
                            # emmc_switch(1)
                            mtk.port.usbwrite(pack(">I", 0xf00dd00d))
                            mtk.port.usbwrite(pack(">I", 0x1002))
                            mtk.port.usbwrite(pack(">I", 0x0))
                            # stat=mtk.port.usbread(4)

                            # kick-wdt
                            #mtk.port.usbwrite(pack(">I", 0xf00dd00d))
                            #.port.usbwrite(pack(">I", 0x3001))

                            # emmc_read(0)
                            mtk.port.usbwrite(pack(">I", 0xf00dd00d))
                            mtk.port.usbwrite(pack(">I", 0x1000))
                            mtk.port.usbwrite(pack(">I", 0x1))
                            #time.sleep(2)
                            data = mtk.port.usbread(0x200,0x200)

                            with open("rpmb", "wb") as wf:
                                for addr in range(0, 0xFFFF):
                                    mtk.port.usbwrite(pack(">I", 0xf00dd00d))
                                    mtk.port.usbwrite(pack(">I", 0x2000))
                                    mtk.port.usbwrite(pack(">I", addr))
                                    tmp = mtk.port.usbread(0x100, 0x100)
                                    if len(tmp) != 0x100:
                                        print("Error on getting data")
                                    wf.write(tmp)
                            print("Done")
                            """
                    else:
                        self.error("Error on jumping to pl")
                        return
                else:
                    self.error("Error on sending pl")
                    return
            self.close()
        elif self.args["peek"]:
            addr = getint(self.args["<offset>"])
            length = getint(self.args["<length>"])
            if self.args["--preloader"] is None:
                preloader = "umidigi_power_preloader_patched"
            else:
                preloader = self.args["--preloader"]
            if self.args["--filename"] is None:
                filename = ""
            else:
                filename = self.args["--filename"]
            if os.path.exists(preloader):
                with open(preloader, "rb") as rf:
                    magic = unpack("<I", rf.read(4))[0]
                    if magic == 0x014D4D4D:
                        rf.seek(0x1C)
                        daaddr = unpack("<I", rf.read(4))[0]
                        dasize = unpack("<I", rf.read(4))[0]
                        maxsize = unpack("<I", rf.read(4))[0]
                        content_offset = unpack("<I", rf.read(4))[0]
                        sig_length = unpack("<I", rf.read(4))[0]
                        jump_offset = unpack("<I", rf.read(4))[0]
                        daaddr = jump_offset + daaddr
                        rf.seek(jump_offset)
                        dadata = rf.read(dasize - jump_offset)
                    else:
                        daaddr = 0x201000
                        rf.seek(0)
                        dadata = rf.read()
            if mtk.preloader.init(args=self.args, readsocid=readsocid):
                # mtk = self.crasher(mtk=mtk, enforcecrash=enforcecrash)
                if mtk.port.cdc.pid == 0x0003:
                    if mtk.preloader.send_da(daaddr, len(dadata), 0x100, dadata):
                        self.info(f"Sent da to {hex(daaddr)}, length {hex(len(dadata))}")
                        if mtk.preloader.jump_da(daaddr):
                            self.info(f"Jumped to {hex(daaddr)}.")
                            # time.sleep(2)
                            mtk = Mtk(loader=self.args["--loader"], loglevel=self.__logger.level, vid=vid, pid=pid,
                                      interface=interface,
                                      args=self.args)
                            res = mtk.preloader.init(args=self.args, readsocid=readsocid)
                            if not res:
                                self.error("Error on loading preloader")
                                return
                            else:
                                self.info("Successfully connected to pl.")
                                mtk.port.usbwrite(mtk.preloader.Cmd.GET_ME_ID.value)  # 0xE1
                                if mtk.port.usbread(1) == mtk.preloader.Cmd.GET_ME_ID.value:
                                    rlength = unpack(">I", mtk.port.usbread(4))[0]
                                    mtk.config.meid = mtk.port.usbread(rlength)
                                    status = unpack("<H", mtk.port.usbread(2))[0]
                        else:
                            self.error("Error on jumping to pl")
                            return
                    else:
                        self.error("Error on sending pl")
                        return
            dwords = length // 4
            if length % 4:
                dwords += 1
            data = mtk.preloader.read32(addr, dwords)
            res = b""
            for value in data:
                res += pack("<I", value)
            if filename == "":
                print(hexlify(res).decode('utf-8'))
            else:
                with open(filename, "wb") as wf:
                    wf.write(res)
                    self.info(f"Data from {hex(addr)} with size of {hex(length)} was written to " + filename)
            self.close()
        elif self.args["stage"]:
            if self.args["--filename"] is None:
                stage1file = "payloads/generic_stage1_payload.bin"
            else:
                stage1file = self.args["--filename"]
            if not os.path.exists(stage1file):
                self.error(f"Error: {stage1file} doesn't exist !")
                return False
            if self.args["--stage2addr"] is None:
                stage2addr = None
            else:
                stage2addr = getint(self.args["--stage2addr"])
            if self.args["--stage2"] is None:
                stage2file = os.path.join("payloads", "stage2.bin")
            else:
                stage2file = self.args["--stage2"]
                if not os.path.exists(stage2file):
                    self.error(f"Error: {stage2file} doesn't exist !")
                    return False
            verifystage2 = self.args["--verifystage2"]
            if mtk.preloader.init(args=self.args, readsocid=readsocid):
                if self.args["--crash"] is not None:
                    mtk = self.crasher(rmtk=mtk, readsocid=readsocid, enforcecrash=enforcecrash)
                if mtk.port.cdc.pid == 0x0003:
                    plt = PLTools(mtk, self.__logger.level)
                    self.info("Uploading stage 1")
                    if plt.runpayload(filename=stage1file, ptype="kamakiri"):
                        self.info("Successfully uploaded stage 1, sending stage 2")
                        with open(stage2file, "rb") as rr:
                            stage2data = rr.read()
                            while len(stage2data) % 0x200:
                                stage2data += b"\x00"
                        if stage2addr is None:
                            stage2addr = mtk.config.chipconfig.da_payload_addr
                            if stage2addr is None:
                                stage2addr = 0x201000

                        # ###### Send stage2
                        # magic
                        mtk.port.usbwrite(pack(">I", 0xf00dd00d))
                        # cmd write
                        mtk.port.usbwrite(pack(">I", 0x4000))
                        # address
                        mtk.port.usbwrite(pack(">I", stage2addr))
                        # length
                        mtk.port.usbwrite(pack(">I", len(stage2data)))
                        bytestowrite = len(stage2data)
                        pos = 0
                        while bytestowrite > 0:
                            size = min(bytestowrite, 1)
                            if mtk.port.usbwrite(stage2data[pos:pos + size]):
                                bytestowrite -= size
                                pos += size
                        mtk.port.usbwrite(b"")
                        time.sleep(0.1)
                        flag = mtk.port.rdword()
                        if flag != 0xD0D0D0D0:
                            self.error(f"Error on sending stage2, size {hex(len(stage2data))}.")
                        self.info(f"Done sending stage2, size {hex(len(stage2data))}.")

                        if verifystage2:
                            self.info("Verifying stage2 data")
                            rdata = b""
                            mtk.port.usbwrite(pack(">I", 0xf00dd00d))
                            mtk.port.usbwrite(pack(">I", 0x4002))
                            mtk.port.usbwrite(pack(">I", stage2addr))
                            mtk.port.usbwrite(pack(">I", len(stage2data)))
                            bytestoread = len(stage2data)
                            while bytestoread > 0:
                                size = min(bytestoread, 64)
                                rdata += mtk.port.usbread(size)
                                bytestoread -= size
                            flag = mtk.port.rdword()
                            if flag != 0xD0D0D0D0:
                                self.error("Error on reading stage2 data")
                            if rdata != stage2data:
                                self.error("Stage2 data doesn't match")
                                with open("rdata", "wb") as wf:
                                    wf.write(rdata)
                            else:
                                self.info("Stage2 verification passed.")

                        # ####### Kick Watchdog
                        # magic
                        # mtk.port.usbwrite(pack("<I", 0xf00dd00d))
                        # cmd kick_watchdog
                        # mtk.port.usbwrite(pack("<I", 0x3001))

                        # ######### Jump stage1
                        # magic
                        mtk.port.usbwrite(pack(">I", 0xf00dd00d))
                        # cmd jump
                        mtk.port.usbwrite(pack(">I", 0x4001))
                        # address
                        mtk.port.usbwrite(pack(">I", stage2addr))
                        self.info("Done jumping stage2")
                        ack = unpack(">I", mtk.port.usbread(4))[0]
                        if ack == 0xB1B2B3B4:
                            self.info("Successfully loaded stage2")
                            """
                            # emmc_switch(1)
                            mtk.port.usbwrite(pack(">I", 0xf00dd00d))
                            mtk.port.usbwrite(pack(">I", 0x1002))
                            mtk.port.usbwrite(pack(">I", 0x1))
                            # stat=mtk.port.usbread(4)

                            # kick-wdt
                            mtk.port.usbwrite(pack(">I", 0xf00dd00d))
                            mtk.port.usbwrite(pack(">I", 0x3001))

                            # emmc_read(0)
                            mtk.port.usbwrite(pack(">I", 0xf00dd00d))
                            mtk.port.usbwrite(pack(">I", 0x1000))
                            mtk.port.usbwrite(pack(">I", 0x0))
                            data = mtk.port.usbread(0x200,0x200)

                            data = b""
                            with open("rpmb", "wb") as wf:
                                for addr in range(0, 4 * 1024 * 1024 // 0x100):
                                    mtk.port.usbwrite(pack(">I", 0xf00dd00d))
                                    mtk.port.usbwrite(pack(">I", 0x2000))
                                    mtk.port.usbwrite(pack(">H", addr))
                                    tmp = mtk.port.usbread(0x100, 0x100)
                                    tmp=tmp[::-1]
                                    if len(tmp) != 0x100:
                                        print("Error on getting data")
                                    wf.write(tmp)
                            print("Done")
                            # print(hexlify(data).decode('utf-8'))
                        """
                        # mtk = Mtk(loader=args["--loader"], loglevel=self.__logger.level, vid=vid, pid=pid,
                        # interface=interface,    args=args)
                        # res=mtk.preloader.init(args)
                        # if not res:
                        #    print("Error on loading preloader")
                self.close()
            else:
                mtk.port.close()
                return False
        elif self.args["payload"]:
            if mtk.preloader.init(args=self.args, readsocid=readsocid):
                mtk = self.crasher(rmtk=mtk, readsocid=readsocid, enforcecrash=enforcecrash)
                plt = PLTools(mtk, self.__logger.level)
                payloadfile = self.args["--payload"]
                if payloadfile is None:
                    payloadfile = "payloads/generic_patcher_payload.bin"
                if self.args["--ptype"] == "amonet":
                    plt.runpayload(filename=payloadfile, ptype="amonet")
                elif self.args["--ptype"] == "kamakiri":
                    plt.runpayload(filename=payloadfile, ptype="kamakiri")
                else:
                    plt.runpayload(filename=payloadfile, ptype="")
            mtk.port.close()
            self.close()
        elif self.args["gettargetconfig"]:
            if mtk.preloader.init(args=self.args, readsocid=readsocid):
                self.info("Getting target info...")
                mtk.preloader.get_target_config()
            mtk.port.close()
            self.close()
        else:
            if mtk.preloader.init(args=self.args, readsocid=readsocid):
                if mtk.config.target_config["daa"]:
                    mtk = self.crasher(rmtk=mtk, readsocid=readsocid, enforcecrash=enforcecrash)
                    plt = PLTools(mtk, self.__logger.level)
                    payloadfile = self.args["--payload"]
                    if payloadfile is None:
                        payloadfile = "payloads/generic_patcher_payload.bin"
                    if plt.runpayload(filename=payloadfile, ptype="kamakiri"):
                        mtk.port.close()
                        time.sleep(0.1)
                        mtk = Mtk(loader=self.args["--loader"], loglevel=self.__logger.level, vid=vid, pid=pid,
                                  interface=interface, args=self.args)
                        mtk.preloader.init(args=self.args, readsocid=readsocid)
                    else:
                        self.error("Error on running kamakiri payload")
                if not mtk.daloader.upload_da():
                    self.error("Error uploading da")
                    return False
            else:
                return False

        if self.args["gpt"]:
            directory = self.args["<directory>"]
            if directory is None:
                directory = ""

            sfilename = os.path.join(directory, f"gpt_main.bin")
            data, guid_gpt = mtk.daloader.get_gpt(self.args)
            if guid_gpt is None:
                self.error("Error reading gpt")
                mtk.daloader.close()
                exit(1)
            else:
                with open(sfilename, "wb") as wf:
                    wf.write(data)

                print(f"Dumped GPT from to {sfilename}")
                sfilename = os.path.join(directory, f"gpt_backup.bin")
                with open(sfilename, "wb") as wf:
                    wf.write(data[mtk.daconfig.pagesize:])
                print(f"Dumped Backup GPT to {sfilename}")
            mtk.daloader.close()
            self.close()
        elif self.args["printgpt"]:
            data, guid_gpt = mtk.daloader.get_gpt(self.args)
            if guid_gpt is None:
                self.error("Error reading gpt")
            else:
                guid_gpt.print()
            mtk.daloader.close()
            self.close()
        elif self.args["r"]:
            partitionname = self.args["<partitionname>"]
            parttype = self.args["--parttype"]
            filename = self.args["<filename>"]
            filenames = filename.split(",")
            partitions = partitionname.split(",")
            if len(partitions) != len(filenames):
                self.error("You need to gives as many filenames as given partitions.")
                mtk.daloader.close()
                exit(1)
            if parttype == "user" or parttype is None:
                i = 0
                for partition in partitions:
                    partfilename = filenames[i]
                    i += 1
                    res = mtk.daloader.detect_partition(self.args, partition, parttype)
                    if res[0]:
                        rpartition = res[1]
                        mtk.daloader.readflash(addr=rpartition.sector * mtk.daloader.daconfig.pagesize,
                                               length=rpartition.sectors * mtk.daloader.daconfig.pagesize,
                                               filename=partfilename, parttype=parttype)
                        print(f"Dumped sector {str(rpartition.sector)} with sector count " +
                              f"{str(rpartition.sectors)} as {partfilename}.")
                    else:
                        self.error(f"Error: Couldn't detect partition: {partition}\nAvailable partitions:")
                        for rpartition in res[1]:
                            self.info(rpartition.name)
            else:
                i = 0
                for partfilename in filenames:
                    pos = 0
                    mtk.daloader.readflash(addr=pos, length=0xFFFFFFFF, filename=partfilename, parttype=parttype)
                    print(f"Dumped partition {str(partitionname)} as {partfilename}.")
                    i += 1
            mtk.daloader.close()
            self.close()
        elif self.args["rl"]:
            directory = self.args["<directory>"]
            parttype = self.args["--parttype"]
            if self.args["--skip"]:
                skip = self.args["--skip"].split(",")
            else:
                skip = []
            if not os.path.exists(directory):
                os.mkdir(directory)
            data, guid_gpt = mtk.daloader.get_gpt(self.args, parttype=parttype)
            if guid_gpt is None:
                self.error("Error reading gpt")
            else:
                storedir = directory
                if not os.path.exists(storedir):
                    os.mkdir(storedir)
                sfilename = os.path.join(storedir, f"gpt_main.bin")
                with open(sfilename, "wb") as wf:
                    wf.write(data)

                sfilename = os.path.join(storedir, f"gpt_backup.bin")
                with open(sfilename, "wb") as wf:
                    wf.write(data[mtk.daconfig.pagesize * 2:])

                for partition in guid_gpt.partentries:
                    partitionname = partition.name
                    if partition.name in skip:
                        continue
                    filename = os.path.join(storedir, partitionname + ".bin")
                    self.info(f"Dumping partition {str(partition.name)} with sector count {str(partition.sectors)} " +
                              "as {filename}.")
                    mtk.daloader.readflash(addr=partition.sector * mtk.daloader.daconfig.pagesize,
                                           length=partition.sectors * mtk.daconfig.pagesize, filename=filename,
                                           parttype=parttype)
            mtk.daloader.close()
            self.close()
        elif self.args["rf"]:
            filename = self.args["<filename>"]
            parttype = self.args["--parttype"]
            length = mtk.daloader.daconfig.flashsize
            print(f"Dumping sector 0 with flash size {hex(length)} as {filename}.")
            mtk.daloader.readflash(addr=0, length=length, filename=filename, parttype=parttype)
            print(f"Dumped sector 0 with flash size {hex(length)} as {filename}.")
            mtk.daloader.close()
            self.close()
        elif self.args["rs"]:
            start = getint(self.args["<start_sector>"])
            sectors = getint(self.args["<sectors>"])
            filename = self.args["<filename>"]
            parttype = self.args["--parttype"]
            mtk.daloader.readflash(addr=start * mtk.daloader.daconfig.pagesize,
                                   length=sectors * mtk.daloader.daconfig.pagesize,
                                   filename=filename, parttype=parttype)
            print(f"Dumped sector {str(start)} with sector count {str(sectors)} as {filename}.")
            mtk.daloader.close()
            self.close()
        elif self.args["footer"]:
            filename = self.args["<filename>"]
            data, guid_gpt = mtk.daloader.get_gpt(self.args)
            if guid_gpt is None:
                self.error("Error reading gpt")
                mtk.daloader.close()
                exit(1)
            else:
                pnames = ["userdata2", "metadata", "userdata", "reserved1", "reserved2", "reserved3"]
                for partition in guid_gpt.partentries:
                    if partition.name in pnames:
                        print(f"Detected partition: {partition.name}")
                        if partition.name in ["userdata2", "userdata"]:
                            data = mtk.daloader.readflash(
                                (partition.sector + partition.sectors) * mtk.daloader.daconfig.pagesize - 0x4000,
                                0x4000, "", False)
                        else:
                            data = mtk.daloader.readflash(partition.sector * mtk.daloader.daconfig.pagesize, 0x4000, "",
                                                          False)
                        if data == b"":
                            continue
                        val = struct.unpack("<I", data[:4])[0]
                        if (val & 0xFFFFFFF0) == 0xD0B5B1C0:
                            with open(filename, "wb") as wf:
                                wf.write(data)
                                print(f"Dumped footer from {partition.name} as {filename}.")
                                mtk.daloader.close()
                                exit(0)
            self.error(f"Error: Couldn't detect footer partition.")
            mtk.daloader.close()
            self.close()
        elif self.args["w"]:
            partitionname = self.args["<partitionname>"]
            filename = self.args["<filename>"]
            parttype = self.args["--parttype"]
            filenames = filename.split(",")
            partitions = partitionname.split(",")
            if len(partitions) != len(filenames):
                self.error("You need to gives as many filenames as given partitions.")
                mtk.daloader.close()
                exit(0)
            if parttype == "user" or parttype is None:
                i = 0
                for partition in partitions:
                    partfilename = filenames[i]
                    i += 1
                    res = mtk.daloader.detect_partition(self.args, partition, parttype)
                    if res[0]:
                        rpartition = res[1]
                        mtk.daloader.writeflash(addr=rpartition.sector * mtk.daloader.daconfig.pagesize,
                                                length=rpartition.sectors * mtk.daloader.daconfig.pagesize,
                                                filename=partfilename,
                                                partitionname=partition, parttype=parttype)
                        print(
                            f"Wrote {partfilename} to sector {str(rpartition.sector)} with " +
                            f"sector count {str(rpartition.sectors)}.")
                    else:
                        self.error(f"Error: Couldn't detect partition: {partition}\nAvailable partitions:")
                        for rpartition in res[1]:
                            self.info(rpartition.name)
            else:
                pos = 0
                for partfilename in filenames:
                    size = os.stat(partfilename).st_size
                    mtk.daloader.writeflash(addr=pos, length=size, filename=partfilename, partitionname=partitionname,
                                            parttype=parttype)
                    print(f"Wrote {partfilename} to sector {str(pos // 0x200)} with " +
                          f"sector count {str(size)}.")
                    psize = size // 0x200 * 0x200
                    if size % 0x200 != 0:
                        psize += 0x200
                    pos += psize
            mtk.daloader.close()
            self.close()
        elif self.args["e"]:
            partitionname = self.args["<partitionname>"]
            parttype = self.args["--parttype"]
            partitions = partitionname.split(",")
            if parttype == "user" or parttype is None:
                i = 0
                for partition in partitions:
                    i += 1
                    res = mtk.daloader.detect_partition(self.args, partition, parttype)
                    if res[0]:
                        rpartition = res[1]
                        mtk.daloader.formatflash(addr=rpartition.sector * mtk.daloader.daconfig.pagesize,
                                                 length=rpartition.sectors * mtk.daloader.daconfig.pagesize,
                                                 partitionname=partition, parttype=parttype)
                        print(
                            f"Formatted sector {str(rpartition.sector)} with " +
                            f"sector count {str(rpartition.sectors)}.")
                    else:
                        self.error(f"Error: Couldn't detect partition: {partition}\nAvailable partitions:")
                        for rpartition in res[1]:
                            self.info(rpartition.name)
            else:
                pos = 0
                for partitionname in partitions:
                    mtk.daloader.formatflash(addr=pos, length=0xF000000, partitionname=partitionname, parttype=parttype,
                                             display=True)
                    print(f"Formatted sector {str(pos // 0x200)}")
            mtk.daloader.close()
            self.close()
        elif self.args["wf"]:
            filename = self.args["<filename>"]
            parttype = self.args["--parttype"]
            filenames = filename.split(",")
            pos = 0
            for partfilename in filenames:
                size = os.stat(partfilename).st_size // 0x200 * 0x200
                mtk.daloader.writeflash(addr=pos,
                                        length=size,
                                        filename=partfilename,
                                        partitionname=None, parttype=parttype)
                print(f"Wrote {partfilename} to sector {str(pos // 0x200)} with " +
                      f"sector count {str(size // 0x200)}.")
            mtk.daloader.close()
            self.close()
        elif self.args["reset"]:
            mtk.daloader.close()
            self.close()


if __name__ == '__main__':
    print("MTK Flash/Exploit Client V1.2 (c) B.Kerler 2020-2021")
    mtk = Main().run()
