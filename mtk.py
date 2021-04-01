#!/usr/bin/env python3
# !/usr/bin/env python3
# MTK Flash Client (c) B.Kerler 2020-2021.
# Licensed under MIT License
"""
Usage:
    mtk.py -h | --help
    mtk.py dumpbrom [--filename=filename] [--ptype=ptype] [--crash] [--skipwdt] [--wdt=wdt] [--var1=var1] [--da_addr=addr] [--brom_addr=addr] [--uartaddr=addr] [--debugmode] [--vid=vid] [--pid=pid] [--interface=interface]
    mtk.py crash [--mode=mode] [--debugmode] [--skipwdt] [--vid=vid] [--pid=pid]
    mtk.py gettargetconfig [--debugmode] [--vid=vid] [--pid=pid]

Description:
    dumpbrom [--wdt=wdt] [--var1=var1] [--payload_addr=addr]                                 # Try to dump the bootrom
    crash [--mode] [--debugmode] [--vid=vid] [--pid=pid]                                     # Try to crash the preloader
    gettargetconfig [--debugmode]                                                            # Get target config (sbc, daa, etc.)

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
"""

from docopt import docopt

from config.usb_ids import default_ids
from Library.pltools import PLTools
from Library.mtk_preloader import Preloader
from Library.Port import Port
from Library.utils import *
from config.brom_config import Mtk_Config

args = docopt(__doc__, version='EDL 2.1')

logger = logging.getLogger(__name__)


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
        self.preloader = Preloader(self, self.__logger.level)

class Main(metaclass=LogBase):
    def __init__(self):
        self.__logger = self.__logger
        self.info = self.__logger.info
        self.error = self.__logger.error
        self.warning = self.__logger.warning

    def close(self):
        sys.exit(0)

    def crasher(self, mtk, enforcecrash, display=True, mode=None):
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
                    mtk = Mtk(loader=None, loglevel=self.__logger.level, vid=0xE8D, pid=0x0003, interface=1,
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
                mtk = Mtk(loader=None, loglevel=self.__logger.level, vid=0xE8D, pid=0x0003, interface=1,
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
        mtk = Mtk(loader=None, loglevel=self.__logger.level, vid=vid, pid=pid, interface=interface,
                  args=args)

        if args["dumpbrom"]:
            if mtk.preloader.init(args):
                mtk = self.crasher(mtk=mtk, enforcecrash=enforcecrash)
                if mtk is None:
                    sys.exit(0)
                if mtk.port.cdc.vid != 0xE8D and mtk.port.cdc.pid != 0x0003:
                    self.warning("We couldn't enter preloader.")
                filename = args["--filename"]
                if filename is None:
                    cpu = ""
                    if mtk.config.cpu != "":
                        cpu = "_" + mtk.config.cpu
                    filename = "brom" + cpu + "_" + hex(mtk.config.hwcode)[2:] + ".bin"
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


if __name__ == '__main__':
    print("MTK Flash/Exploit Client V1.2 (c) B.Kerler 2020-2021")
    mtk = Main().run()
