#!/usr/bin/env python3
import os
import logging
import sys
import argparse
from binascii import hexlify
from struct import pack, unpack
from Library.usblib import usb_class
from Library.utils import LogBase
from Library.utils import print_progress


class Stage2(metaclass=LogBase):
    def __init__(self, args, loglevel=logging.INFO):
        self.__logger = self.__logger
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
        portconfig = [[0x0E8D, 0x0003, -1], [0x0E8D, 0x2000, -1]]
        self.cdc = usb_class(portconfig=portconfig, loglevel=loglevel, devclass=10)

    def connect(self):
        self.cdc.connected = self.cdc.connect()
        return self.cdc.connected

    def close(self):
        if self.cdc.connected:
            self.cdc.close()

    def readflash(self, type: int, start, length, display=False, filename: str = None):
        wf = None
        buffer = bytearray()
        if filename is not None:
            wf = open(filename, "wb")
        sectors = (length // 0x200) + (1 if length % 0x200 else 0)
        startsector = (start // 0x200)
        # emmc_switch(1)
        self.cdc.usbwrite(pack(">I", 0xf00dd00d))
        self.cdc.usbwrite(pack(">I", 0x1002))
        self.cdc.usbwrite(pack(">I", type))

        if display:
            print_progress(0, 100, prefix='Progress:', suffix='Complete', bar_length=50)

        # kick-wdt
        # self.cdc.usbwrite(pack(">I", 0xf00dd00d))
        # self.cdc.usbwrite(pack(">I", 0x3001))

        bytestoread = sectors * 0x200
        bytesread = 0
        old = 0
        # emmc_read(0)
        for sector in range(startsector, sectors):
            self.cdc.usbwrite(pack(">I", 0xf00dd00d))
            self.cdc.usbwrite(pack(">I", 0x1000))
            self.cdc.usbwrite(pack(">I", sector))
            tmp = self.cdc.usbread(0x200, 0x200)
            if len(tmp) != 0x200:
                self.error("Error on getting data")
                return
            if display:
                prog = sector / sectors * 100
                if round(prog, 1) > old:
                    print_progress(prog, 100, prefix='Progress:',
                                   suffix='Complete, Sector:' + hex((sectors * 0x200) - bytestoread),
                                   bar_length=50)
                    old = round(prog, 1)
            bytesread += len(tmp)
            size = min(bytestoread, len(tmp))
            if wf is not None:
                wf.write(tmp[:size])
            else:
                buffer.extend(tmp)
            bytestoread -= size
        if display:
            print_progress(100, 100, prefix='Complete: ', suffix=filename, bar_length=50)
        if wf is not None:
            wf.close()
        else:
            return buffer[start % 0x200:(start % 0x200) + length]

    def preloader(self, start, length, filename):
        sectors = 0
        if start != 0:
            start = (start // 0x200)
        if length != 0:
            sectors = (length // 0x200) + (1 if length % 0x200 else 0)
        self.info("Reading preloader...")
        if self.cdc.connected:
            if sectors == 0:
                buffer = self.readflash(type=1, start=0, length=0x1000, display=False)
                if len(buffer) != 0x1000:
                    print("Error on reading boot1 area.")
                    return
                if buffer[:9] == b'EMMC_BOOT':
                    startbrlyt = unpack("<I", buffer[0x10:0x14])[0]
                    if buffer[startbrlyt:startbrlyt + 5] == b"BRLYT":
                        start = unpack("<I", buffer[startbrlyt + 0xC:startbrlyt + 0xC + 4])[0]
                        if buffer[start:start + 4] == b"MMM\x01":
                            length = unpack("<I", buffer[start + 0x20:start + 0x24])[0]
                            self.readflash(type=1, start=start, length=length, display=True, filename=filename)
                            print("Done")
                            return
                print("Error on getting preloader info, aborting.")
            else:
                self.readflash(type=1, start=start, length=length, display=True, filename=filename)
            print("Done")

    def memread(self, start, length, filename):
        bytestoread = length
        addr = start
        data = b""
        pos = 0
        if filename is not None:
            wf = open(filename, "wb")
        while bytestoread > 0:
            size = min(bytestoread, 0x200)
            self.cdc.usbwrite(pack(">I", 0xf00dd00d))
            self.cdc.usbwrite(pack(">I", 0x4000))
            self.cdc.usbwrite(pack(">I", addr + pos))
            self.cdc.usbwrite(pack(">I", size))
            if filename is not None:
                data += self.cdc.usbread(size, size)
            else:
                wf.write(self.cdc.usbwrite(size, size))
            bytestoread -= size
            pos += size
        self.info(f"{hex(start)}: " + hexlify(data).decode('utf-8'))
        if filename is not None:
            wf.close()

    def memwrite(self, start, data, filename):
        if filename is not None:
            rf = open(filename, "rb")
            bytestowrite = os.stat(filename).st_size
        else:
            if isinstance(data, str):
                data = bytes.fromhex(data)
            elif isinstance(data, int):
                data = pack("<I", data)
            bytestowrite = len(data)
        addr = start
        pos = 0
        while bytestowrite > 0:
            size = min(bytestowrite, 0x200)
            self.cdc.usbwrite(pack(">I", 0xf00dd00d))
            self.cdc.usbwrite(pack(">I", 0x4002))
            self.cdc.usbwrite(pack(">I", addr + pos))
            self.cdc.usbwrite(pack(">I", size))
            if filename is None:
                self.cdc.usbwrite(data[pos:pos + 4])
            else:
                self.cdc.usbwrite(rf.read(4))
            bytestowrite -= size
            pos += size
        ack = self.cdc.usbread(4)
        if ack == b"\xD0\xD0\xD0\xD0":
            self.info(f"Successfully wrote data to {hex(start)}.")
        else:
            self.info(f"Failed to write data to {hex(start)}.")
        if filename is not None:
            rf.close()

    def rpmb(self, start, length, filename):
        if start == 0:
            start = 0
        else:
            start = (start // 0x100)
        if length == 0:
            sectors = 4 * 1024 * 1024 // 0x100
        else:
            sectors = (length // 0x100) + (1 if length % 0x100 else 0)
        self.info("Reading rpmb...")

        self.cdc.usbwrite(pack(">I", 0xf00dd00d))
        self.cdc.usbwrite(pack(">I", 0x1002))
        self.cdc.usbwrite(pack(">I", 0x1))

        # kick-wdt
        self.cdc.usbwrite(pack(">I", 0xf00dd00d))
        self.cdc.usbwrite(pack(">I", 0x3001))

        print_progress(0, 100, prefix='Progress:', suffix='Complete', bar_length=50)
        bytesread = 0
        old = 0
        bytestoread = sectors * 0x100
        with open(filename, "wb") as wf:
            for sector in range(start, sectors):
                self.cdc.usbwrite(pack(">I", 0xf00dd00d))
                self.cdc.usbwrite(pack(">I", 0x2000))
                self.cdc.usbwrite(pack(">H", sector))
                tmp = self.cdc.usbread(0x100, 0x100)[::-1]
                if len(tmp) != 0x100:
                    self.error("Error on getting data")
                    return
                prog = sector / sectors * 100
                if round(prog, 1) > old:
                    print_progress(prog, 100, prefix='Progress:',
                                   suffix='Complete, Sector:' + hex((sectors * 0x200) - bytestoread),
                                   bar_length=50)
                    old = round(prog, 1)
                bytesread += 0x100
                size = min(bytestoread, len(tmp))
                wf.write(tmp[:size])
                bytestoread -= size
            print_progress(100, 100, prefix='Complete: ', suffix=filename, bar_length=50)
        print("Done")


def getint(valuestr):
    if valuestr == '':
        return None
    try:
        return int(valuestr)
    except:
        try:
            return int(valuestr, 16)
        except Exception as err:
            pass
    return 0


def main():
    parser = argparse.ArgumentParser(description='Stage2 client (c) B.Kerler 2021.')
    parser.add_argument('--rpmb', dest='rpmb', action="store_true",
                        help='Dump rpmb')
    parser.add_argument('--preloader', dest='preloader', action="store_true",
                        help='Dump preloader')
    parser.add_argument('--memread', dest='memread', action="store_true",
                        help='Dump memory')
    parser.add_argument('--memwrite', dest='memwrite', action="store_true",
                        help='Write to memory')
    parser.add_argument('--length', dest='length', type=str,
                        help='Max length to dump')
    parser.add_argument('--start', dest='start', type=str,
                        help='Start offset to dump')
    parser.add_argument('--data', dest='data', type=str,
                        help='Data to write')
    parser.add_argument('--filename', dest='filename', type=str,
                        help='Read from / save to filename')
    args = parser.parse_args()

    start = getint(args.start)
    length = getint(args.length)
    if not os.path.exists("logs"):
        os.mkdir("logs")
    st2 = Stage2(args)
    if st2.connect():
        if args.rpmb:
            if args.filename is None:
                filename = os.path.join("logs", "rpmb")
            else:
                filename = args.filename
            st2.rpmb(start, length, filename)
        elif args.preloader:
            if args.filename is None:
                filename = os.path.join("logs", "preloader")
            else:
                filename = args.filename
            st2.preloader(start, length, filename=filename)
        elif args.memread:
            st2.memread(start, length, args.filename)
        elif args.memwrite:
            st2.memwrite(start, args.data, args.filename)
    st2.close()


if __name__ == "__main__":
    main()
