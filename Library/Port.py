import os
import sys
import logging
from Library.utils import LogBase
import usb.core
import time
from Library.usblib import usb_class
from binascii import hexlify
from struct import pack, unpack

class Port(metaclass=LogBase):
    class deviceclass:
        vid = 0
        pid = 0

        def __init__(self, vid, pid):
            self.vid = vid
            self.pid = pid

    def __init__(self,mtk,portconfig,loglevel=logging.INFO):
        self.config=mtk.config
        self.mtk=mtk
        self.cdc = usb_class(portconfig=portconfig, loglevel=loglevel,devclass=10)
        self.info = self.__logger.info
        self.error = self.__logger.error
        self.warning = self.__logger.warning
        self.debug = self.__logger.debug
        if loglevel == logging.DEBUG:
            logfilename = "log.txt"
            if os.path.exists(logfilename):
                os.remove(logfilename)
            fh = logging.FileHandler(logfilename)
            self.__logger.addHandler(fh)
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger.setLevel(logging.INFO)

    def detectusbdevices(self):
        dev = usb.core.find(find_all=True)
        ids = [self.deviceclass(cfg.idVendor, cfg.idProduct) for cfg in dev]
        return ids

    def usbwrite(self, data):
        size = self.cdc.write(data, len(data))
        # port->flush()
        return size

    def close(self):
        self.cdc.close()
        self.cdc.connected=False

    def usbreadwrite(self, data, resplen):
        size = self.usbwrite(data)
        # port->flush()
        res = self.usbread(resplen)
        return res

    def rdword(self,count=1):
        data=unpack(">"+"I"*count,self.mtk.port.usbread(4*count))
        if count==1:
            return data[0]
        return data

    def rword(self,count=1):
        data=[unpack(">H",self.mtk.port.usbread(2))[0] for i in range(count)]
        if count==1:
            return data[0]
        return data

    def rbyte(self,count=1):
        return self.mtk.port.usbread(count)

    def usbread(self, resplen,usbsize=64):
        size=min(resplen,usbsize)
        res = b""
        timeout = 0
        while resplen > 0:
            tmp = self.cdc.read(size)
            if tmp == b"":
                if timeout == 4:
                    break
                timeout += 1
                time.sleep(0.1)
            resplen -= len(tmp)
            res += tmp
        return res

    def posthandshake(self):
        startcmd = [b"\xa0", b"\x0a", b"\x50", b"\x05"]
        length = len(startcmd)
        tries=100
        i=0
        while i < length and tries > 0:
            if self.cdc.device.write(self.cdc.EP_OUT,startcmd[i]):
                time.sleep(0.01)
                v=self.cdc.device.read(self.cdc.EP_IN, 64, None)
                if len(v)==1:
                    if v[0]==~(startcmd[i][0]) & 0xFF:
                        i+=1
                    else:
                        i=0
                        self.cdc.setbreak()
                        self.cdc.setLineCoding(self.config.baudrate)
                        tries-=1
        print()
        self.info("Device detected :)")
        return True


    def handshake(self, maxtries=None, loop=0):
        counter=0
        startcmd = [b"\xa0", b"\x0a", b"\x50", b"\x05"]
        length = len(startcmd)

        while not self.cdc.connected:
            try:
                if maxtries!=None:
                    if counter==maxtries:
                        break
                counter+=1
                self.cdc.connected = self.cdc.connect()
                if self.cdc.connected:
                    #self.cdc.setLineCoding(19200)
                    #self.cdc.setControlLineState(RTS=True,DTR=True)
                    #self.cdc.setbreak()
                    tries = 100
                    i = 0
                    #self.cdc.setLineCoding(115200)
                    #self.cdc.setbreak()
                    while i < length and tries > 0:
                        v=b""
                        if self.cdc.device.write(self.cdc.EP_OUT,startcmd[i]):
                            time.sleep(0.01)
                            try:
                                v=self.cdc.device.read(self.cdc.EP_IN, 64, None)
                                if len(v) == 1:
                                    if v[0] == ~(startcmd[i][0]) & 0xFF:
                                        i += 1
                                    else:
                                        i = 0
                                        self.cdc.setbreak()
                                        self.cdc.setLineCoding(self.config.baudrate)
                                        tries -= 1
                            except:
                                self.debug("Timeout")
                                i = 0
                                time.sleep(0.005)

                        """
                        if len(v) < 1:
                            self.debug("Timeout")
                            i = 0
                            time.sleep(0.005)
                        """
                    print()
                    self.info("Device detected :)")
                    return True
                else:
                    sys.stdout.write('.')
                    if loop >= 20:
                        sys.stdout.write('\n')
                        loop = 0
                    loop += 1
                    time.sleep(0.3)
                    sys.stdout.flush()
            except:
                pass
        return False

    def mtk_cmd(self, value, bytestoread=0, nocmd=False):
        resp = b""
        dlen = len(value)
        wr = self.usbwrite(value)
        if wr:
            if nocmd:
                cmdrsp = self.usbread(bytestoread)
                return cmdrsp
            else:
                cmdrsp = self.usbread(dlen)
                if cmdrsp[0] is not value[0]:
                    self.error("Cmd error :" + hexlify(cmdrsp).decode('utf-8'))
                    return -1
                if bytestoread > 0:
                    resp = self.usbread(bytestoread)
                return resp
        else:
            self.warning("Couldn't send :"+hexlify(value).decode('utf-8'))
            return resp

    def echo(self, data):
        if isinstance(data, int):
            data=pack(">I",data)
        if isinstance(data, bytes):
            data = [data]
        for val in data:
            self.usbwrite(val)
            tmp = self.usbread(len(val))
            if val != tmp:
                return False
        return True