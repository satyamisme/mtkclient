#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (c) B.Kerler 2018-2021 MIT License
import sys
import logging
import logging.config
import codecs
import struct
import os
import shutil
import stat
import colorama
import copy
from struct import pack, unpack

try:
    from capstone import *
except ImportError as e:
    print(f"Capstone library missing: {str(e)}")

try:
    from keystone import *
except ImportError as e:
    print(f"Keystone library missing: {str(e)}")


def hex2bytes(value):
    return bytes.fromhex(value)


def hex2bytearray(value):
    return bytearray.fromhex(value)


def getint(value):
    if "0x" in value:
        return int(value, 16)
    else:
        return int(value, 10)


def revdword(value):
    return unpack(">I", pack("<I", value))[0]

def getint(valuestr):
    try:
        return int(valuestr)
    except:
        try:
            return int(valuestr, 16)
        except Exception as err:
            pass
    return 0


class ColorFormatter(logging.Formatter):
    LOG_COLORS = {
        logging.ERROR: colorama.Fore.RED,
        logging.DEBUG: colorama.Fore.LIGHTMAGENTA_EX,
        logging.WARNING: colorama.Fore.YELLOW,
    }

    def format(self, record, *args, **kwargs):
        # if the corresponding logger has children, they may receive modified
        # record, so we want to keep it intact
        new_record = copy.copy(record)
        if new_record.levelno in self.LOG_COLORS:
            pad = ""
            if new_record.name != "root":
                print(new_record.name)
                pad = "[LIB]: "
            # we want levelname to be in different color, so let's modify it
            new_record.msg = "{pad}{color_begin}{msg}{color_end}".format(
                pad=pad,
                msg=new_record.msg,
                color_begin=self.LOG_COLORS[new_record.levelno],
                color_end=colorama.Style.RESET_ALL,
            )
        # now we can let standart formatting take care of the rest
        return super(ColorFormatter, self).format(new_record, *args, **kwargs)


class LogBase(type):
    debuglevel = logging.root.level

    def __init__(cls, *args):
        super().__init__(*args)
        logger_attribute_name = '_' + cls.__name__ + '__logger'
        logger_debuglevel_name = '_' + cls.__name__ + '__debuglevel'
        logger_name = '.'.join([c.__name__ for c in cls.mro()[-2::-1]])
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "root": {
                    "()": ColorFormatter,
                    "format": "%(name)s - %(message)s",
                }
            },
            "handlers": {
                "root": {
                    # "level": cls.__logger.level,
                    "formatter": "root",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                }
            },
            "loggers": {
                "": {
                    "handlers": ["root"],
                    # "level": cls.debuglevel,
                    "propagate": False
                }
            },
        }
        logging.config.dictConfig(log_config)
        logger = logging.getLogger(logger_name)

        setattr(cls, logger_attribute_name, logger)
        setattr(cls, logger_debuglevel_name, cls.debuglevel)


def del_rw(action, name, exc):
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)


def rmrf(path):
    if os.path.exists(path):
        if os.path.isfile(path):
            del_rw("", path, "")
        else:
            shutil.rmtree(path, onerror=del_rw)


def uart_valid_sc(sc):
    badchars = [b'\x00', b'\n', b'\r', b'\x08', b'\x7f', b'\x20', b'\x09']
    for idx, c in enumerate(sc):
        c = bytes([c])
        if c in badchars:
            print("bad char 0x%s in SC at offset %d, opcode # %d!\n" % (codecs.encode(c, 'hex'), idx, idx / 4))
            print(codecs.encode(sc, 'hex'))
            return False
    return True


def disasm(code, size):
    cs = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    instr = []
    for i in cs.disasm(code, size):
        # print("0x%x:\t%s\t%s" % (i.address, i.mnemonic, i.op_str))
        instr.append("%s\t%s" % (i.mnemonic, i.op_str))
    return instr


class PatchTools:
    cstyle = False
    bDebug = False

    def __init__(self, bdebug=False):
        self.bDebug = bdebug

    def has_bad_uart_chars(self, data):
        badchars = [b'\x00', b'\n', b'\r', b'\x08', b'\x7f', b'\x20', b'\x09']
        for idx, c in enumerate(data):
            c = bytes([c])
            if c in badchars:
                return True
        return False

    def generate_offset(self, offset):
        div = 0
        found = False
        while not found and div < 0x606:
            data = struct.pack("<I", offset + div)
            data2 = struct.pack("<H", div)
            badchars = self.has_bad_uart_chars(data)
            if not badchars:
                badchars = self.has_bad_uart_chars(data2)
                if not badchars:
                    return div
            div += 4

        # if div is not found within positive offset, try negative offset
        div = 0
        while not found and div < 0x606:
            data = struct.pack("<I", offset - div)
            data2 = struct.pack("<H", div)
            badchars = self.has_bad_uart_chars(data)
            if not badchars:
                badchars = self.has_bad_uart_chars(data2)
                if not badchars:
                    return -div
            div += 4
        return 0

    # Usage: offset, "X24"
    def generate_offset_asm(self, offset, reg):
        div = self.generate_offset(offset)
        abase = ((offset + div) & 0xFFFF0000) >> 16
        a = ((offset + div) & 0xFFFF)
        strasm = ""
        if div > 0:
            strasm += "# " + hex(offset) + "\n"
            strasm += "mov " + reg + ", #" + hex(a) + ";\n"
            strasm += "movk " + reg + ", #" + hex(abase) + ", LSL#16;\n"
            strasm += "sub  " + reg + ", " + reg + ", #" + hex(div) + ";\n"
        else:
            strasm += "# " + hex(offset) + "\n"
            strasm += "mov " + reg + ", #" + hex(a) + ";\n"
            strasm += "movk " + reg + ", #" + hex(abase) + ", LSL#16;\n"
            strasm += "add  " + reg + ", " + reg + ", #" + hex(-div) + ";\n"
        return strasm

    def assembler(self, code):
        ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
        if self.bDebug:
            try:
                encoding, count = ks.asm(code)
            except KsError as kerr:
                print(kerr)
                print(kerr.stat_count)
                print(code[kerr.stat_count:kerr.stat_count + 10])
                exit(0)
                if self.bDebug:
                    # walk every line to find the (first) error
                    for idx, line in enumerate(code.splitlines()):
                        print("%02d: %s" % (idx, line))
                        if len(line) and line[0] != '.':
                            try:
                                encoding, count = ks.asm(line)
                            except Exception as kerr:
                                print("bummer: " + str(kerr))
                else:
                    exit(0)
        else:
            encoding, count = ks.asm(code)

        sc = ""
        count = 0
        out = ""
        for i in encoding:
            if self.cstyle:
                out += ("\\x%02x" % i)
            else:
                out += ("%02x" % i)
            sc += "%02x" % i

            count += 1
            # if bDebug and count % 4 == 0:
            #    out += ("\n")

        return out

    def find_binary(self, data, strf, pos=0):
        t = strf.split(b".")
        pre = 0
        offsets = []
        while pre != -1:
            pre = data[pos:].find(t[0], pre)
            if pre == -1:
                if len(offsets) > 0:
                    for offset in offsets:
                        error = 0
                        rt = offset + len(t[0])
                        for i in range(1, len(t)):
                            if t[i] == b'':
                                rt += 1
                                continue
                            rt += 1
                            prep = data[rt:].find(t[i])
                            if prep != 0:
                                error = 1
                                break
                            rt += len(t[i])
                        if error == 0:
                            return offset
                else:
                    return None
            else:
                offsets.append(pre)
                pre += 1
        return None


def read_object(data: object, definition: object) -> object:
    """
    Unpacks a structure using the given data and definition.
    """
    obj = {}
    object_size = 0
    pos = 0
    for (name, stype) in definition:
        object_size += struct.calcsize(stype)
        obj[name] = struct.unpack(stype, data[pos:pos + struct.calcsize(stype)])[0]
        pos += struct.calcsize(stype)
    obj['object_size'] = object_size
    obj['raw_data'] = data
    return obj


def write_object(definition, *args):
    """
    Unpacks a structure using the given data and definition.
    """
    obj = {}
    object_size = 0
    data = b""
    i = 0
    for (name, stype) in definition:
        object_size += struct.calcsize(stype)
        arg = args[i]
        try:
            data += struct.pack(stype, arg)
        except Exception as err:
            print("Error:" + str(err))
            break
        i += 1
    obj['object_size'] = len(data)
    obj['raw_data'] = data
    return obj


def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix))

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()
