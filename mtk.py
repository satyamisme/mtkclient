#!/usr/bin/env python3
# MTK Flash Client (c) B.Kerler 2020-2021.
# Licensed under MIT License
"""
Usage:
    mtk.py -h | --help
    mtk.py dumpbrom [--nosocid] [--filename=filename] [--ptype=ptype] [--crash] [--skipwdt] [--wdt=wdt] [--var1=var1] [--da_addr=addr] [--brom_addr=addr] [--uartaddr=addr] [--debugmode] [--vid=vid] [--pid=pid] [--interface=interface]
    mtk.py crash [--nosocid] [--mode=mode] [--debugmode] [--skipwdt] [--vid=vid] [--pid=pid]
    mtk.py gettargetconfig [--nosocid] [--debugmode] [--vid=vid] [--pid=pid]
    mtk.py stage [--nosocid] [--stage2=filename] [--stage2addr=addr] [--stage1=filename] [--verifystage2] [--crash]
    mtk.py plstage [--nosocid] [--filename=filename]

Description:
    dumpbrom [--nosocid] [--wdt=wdt] [--var1=var1] [--payload_addr=addr]                                 # Try to dump the bootrom
    crash [--nosocid] [--mode] [--debugmode] [--vid=vid] [--pid=pid]                                     # Try to crash the preloader
    gettargetconfig [--nosocid] [--debugmode]                                                            # Get target config (sbc, daa, etc.)

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
    --nosocid                          Disable socid read
"""

from docopt import docopt
import time
from config.usb_ids import default_ids
from Library.pltools import PLTools
from Library.mtk_preloader import Preloader
from Library.Port import Port
from Library.utils import *
from config.brom_config import Mtk_Config

args = docopt(__doc__, version='MTK 1.2')

logger = logging.getLogger(__name__)


def split_by_n(seq, unit_count):
    """A generator to divide a sequence into chunks of n units."""
    while seq:
        yield seq[:unit_count]
        seq = seq[unit_count:]


class Mtk(metaclass=LogBase):
    def __init__(self, args, loader, nosocid=False, loglevel=logging.INFO, vid=-1, pid=-1, interface=0):
        self.__logger = self.__logger
        self.config = Mtk_Config(self, loglevel)
        self.args = args
        self.info = self.__logger.info
        self.error = self.__logger.error
        self.warning = self.__logger.warning
        if loglevel == logging.DEBUG:
            logfilename = "log.txt"
            if os.path.exists(logfilename):
                os.remove(logfilename)
            fh = logging.FileHandler(logfilename)
            self.__logger.addHandler(fh)
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger.setLevel(logging.INFO)
        da_address = args["--da_addr"]
        if da_address is not None:
            self.config.chipconfig.da_payload_addr = getint(da_address)

        brom_address = args["--brom_addr"]
        if brom_address is not None:
            self.config.chipconfig.brom_payload_addr = getint(brom_address)

        watchdog_address = args["--wdt"]
        if watchdog_address is not None:
            self.config.chipconfig.watchdog = getint(watchdog_address)

        uart_address = args["--uartaddr"]
        if uart_address is not None:
            self.config.chipconfig.uart = getint(uart_address)

        var1 = args["--var1"]
        if var1 is not None:
            self.config.chipconfig.var1 = getint(var1)

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
        self.preloader = Preloader(self, nosocid, self.__logger.level)

class Main(metaclass=LogBase):
    def __init__(self):
        self.__logger = self.__logger
        self.info = self.__logger.info
        self.error = self.__logger.error
        self.warning = self.__logger.warning

    def close(self):
        sys.exit(0)

    def crasher(self, mtk, enforcecrash, display=True, mode=None, nosocid=False):
        plt = PLTools(mtk, self.__logger.level)
        if enforcecrash or not (mtk.port.cdc.vid == 0xE8D and mtk.port.cdc.pid == 0x0003):
            self.info("We're not in bootrom, trying to crash da...")
            if mode is None:
                for crashmode in range(0, 3):
                    try:
                        plt.crash(crashmode)
                    except Exception as e:
                        self.__logger.debug(str(e))
                        pass
                    mtk = Mtk(loader=None, nosocid=nosocid, loglevel=self.__logger.level, vid=0xE8D, pid=0x0003, interface=1,
                              args=args)
                    mtk.preloader.display = display
                    if mtk.preloader.init(args, maxtries=20):
                        break
            else:
                try:
                    plt.crash(mode)
                except Exception as e:
                    self.__logger.debug(str(e))
                    pass
                mtk = Mtk(loader=None, nosocid=nosocid, loglevel=self.__logger.level, vid=0xE8D, pid=0x0003, interface=1,
                          args=args)
                mtk.preloader.display = display
                if mtk.preloader.init(args=args, maxtries=20):
                    return mtk
        return mtk

    def run(self):
        if args["--vid"] is not None:
            vid = getint(args["--vid"])
        else:
            vid = -1
        if args["--pid"] is not None:
            pid = getint(args["--pid"])
        else:
            pid = -1
        if not os.path.exists("logs"):
            os.mkdir("logs")
        if args["--nosocid"] is not None:
            nosocid = args["--nosocid"]
        else:
            nosocid = False
        enforcecrash = False
        if args["--crash"]:
            enforcecrash = True
        if args["--debugmode"]:
            logfilename = "log.txt"
            if os.path.exists(logfilename):
                os.remove(logfilename)
            fh = logging.FileHandler(logfilename)
            self.__logger.addHandler(fh)
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger.setLevel(logging.INFO)
        interface = -1
        mtk = Mtk(loader=None, nosocid=nosocid, loglevel=self.__logger.level, vid=vid, pid=pid, interface=interface,
                  args=args)

        if args["dumpbrom"]:
            if mtk.preloader.init(args):
                mtk = self.crasher(mtk=mtk, enforcecrash=enforcecrash, nosocid=nosocid)
                if mtk is None:
                    sys.exit(0)
                if mtk.port.cdc.vid != 0xE8D and mtk.port.cdc.pid != 0x0003:
                    self.warning("We couldn't enter preloader.")
                filename = args["--filename"]
                if filename is None:
                    cpu = ""
                    if mtk.config.cpu != "":
                        cpu = "_" + mtk.config.cpu
                    filename = os.path.join("logs","brom" + cpu + "_" + hex(mtk.config.hwcode)[2:] + ".bin")
                plt = PLTools(mtk, self.__logger.level)
                plt.run_dump_brom(filename, args["--ptype"])
            mtk.port.close()
            self.close()
        elif args["crash"]:
            if mtk.preloader.init(args):
                self.crasher(mtk=mtk, enforcecrash=enforcecrash, mode=getint(args["--mode"]))
            mtk.port.close()
            self.close()
        elif args["gettargetconfig"]:
            if mtk.preloader.init(args):
                self.info("Getting target info...")
                mtk.preloader.get_target_config()
            mtk.port.close()
            self.close()
        elif args["plstage"]:
            if args["--filename"] is None:
                filename = os.path.join("payloads","pl.bin")
            else:
                filename = args["--filename"]
            if os.path.exists(filename):
                with open(filename, "rb") as rf:
                    rf.seek(0)
                    dadata = rf.read()
            if mtk.preloader.init(args):
                if mtk.config.chipconfig.pl_payload_addr is not None:
                    daaddr = mtk.config.chipconfig.pl_payload_addr
                else:
                    daaddr = 0x40200000  # 0x40001000
                if mtk.preloader.send_da(daaddr, len(dadata), 0x100, dadata):
                    self.info(f"Sent da to {hex(daaddr)}, length {hex(len(dadata))}")
                    if mtk.preloader.jump_da(daaddr):
                        self.info(f"Jumped to {hex(daaddr)}.")
                        ack = unpack(">I", mtk.port.usbread(4))[0]
                        if ack == 0xB1B2B3B4:
                            self.info("Successfully loaded stage2")
        elif args["stage"]:
            if args["--filename"] is None:
                stage1file = "payloads/generic_stage1_payload.bin"
            else:
                stage1file = args["--filename"]
            if not os.path.exists(stage1file):
                self.error(f"Error: {stage1file} doesn't exist !")
                return False
            if args["--stage2addr"] is None:
                stage2addr = 0x201000
            else:
                stage2addr = getint(args["--stage2addr"])
            if args["--stage2"] is None:
                stage2file = "payloads/stage2.bin"
            else:
                stage2file = args["--stage2"]
                if not os.path.exists(stage2file):
                    self.error(f"Error: {stage2file} doesn't exist !")
                    return False
            verifystage2 = args["--verifystage2"]
            if mtk.preloader.init(args):
                if args["--crash"] is not None:
                    mtk = self.crasher(mtk=mtk, enforcecrash=enforcecrash)
                if mtk.port.cdc.pid == 0x0003:
                    plt = PLTools(mtk, self.__logger.level)
                    with open(stage2file, "rb") as rr:
                        stage2data = rr.read()
                        while len(stage2data) % 0x200:
                            stage2data += b"\x00"
                    self.info("Uploading stage 1")
                    if plt.runpayload(filename=stage1file, ptype="kamakiri"):
                        self.info("Sucessfully uploaded stage 1, sending stage 2")
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
                            size = min(bytestowrite, 64)
                            if mtk.port.usbwrite(stage2data[pos:pos + size]):
                                bytestowrite -= size
                                pos += size
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


if __name__ == '__main__':
    print("MTK Flash/Exploit Client V1.2 (c) B.Kerler 2020-2021")
    mtk = Main().run()
