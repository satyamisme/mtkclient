import os
import logging
from Library.utils import LogBase


class damodes:
    DEFAULT = 0
    XFLASH = 1


class chipconfig:
    def __init__(self, var1=None, watchdog=None, uart=None, brom_payload_addr=None,
                 da_payload_addr=None, pl_payload_addr=None, cqdma_base=None, sej_base=None, dxcc_base=None, gcpu_base=None,
                 ap_dma_mem=None, name="", description="", dacode=None, blacklist=(), damode=damodes.DEFAULT):
        self.var1 = var1
        self.watchdog = watchdog
        self.uart = uart
        self.brom_payload_addr = brom_payload_addr
        self.da_payload_addr = da_payload_addr
        self.pl_payload_addr = pl_payload_addr
        self.cqdma_base = cqdma_base
        self.ap_dma_mem = ap_dma_mem
        self.sej_base = sej_base
        self.dxcc_base = dxcc_base
        self.name = name
        self.description = description
        self.dacode = dacode
        self.blacklist = blacklist
        self.gcpu_base = gcpu_base
        self.dacode = dacode
        self.damode = damode


    # Credits to cyrozap and Chaosmaster for some values
    """
    0x0:    chipconfig(var1=0x0,
                       watchdog=0x0,
                       uart=0x0,
                       brom_payload_addr=0x0,
                       da_payload_addr=0x0,
                       cqdma_base=0x0,
                       gcpu_base=0x0,
                       blacklist=[(0x0, 0x0),(0x00105704, 0x0)],
                       dacode=0x0,
                       name=""),
                       
                       Needed fields
                       
                       For hashimoto:
                       cqdma_base,
                       ap_dma_mem,
                       blacklist
                       
                       For kamakiri:
                       var1
                       
                       For amonet:
                       gpu_base
                       blacklist
    """


hwconfig = {
    0x5700: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        # da_payload_addr
        gcpu_base=0x10016000,
        # sej_base
        # no dxcc
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.DEFAULT,
        # dacode
        name="MT5700"),
    0x2503: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        # da_payload_addr
        # gcpu_base
        sej_base=0x80140000,
        # no dxcc
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.DEFAULT,
        # dacode
        name="MT2503"),
    0x6255: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        # da_payload_addr
        # gcpu_base
        sej_base=0x80140000,
        # no dxcc
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.DEFAULT,
        # dacode
        name="MT6255"),
    0x6280: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        # da_payload_addr
        # gcpu_base
        sej_base=0x80080000,
        # no dxcc
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.DEFAULT,
        name="MT6280"),
    0x2601: chipconfig(  # var1
        # uart
        # brom_payload_addr
        watchdog=0x10007000,
        da_payload_addr=0x2007000,
        # gcpu_base
        # sej_base
        # no dxcc
        # cqdma_base
        # ap_dma_mem
        # blacklist
        dacode=0x2601,
        damode=damodes.DEFAULT,  #
        name="MT2601"),
    0x3967: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        da_payload_addr=0x200000,
        # gcpu_base
        # sej_base
        # no dxcc
        # cqdma_base
        # ap_dma_mem
        # blacklist
        dacode=0x3967,
        damode=damodes.DEFAULT,
        name="MT3967"),
    0x6261: chipconfig(var1=0x28,   # Smartwatch, confirmed
                       watchdog=0xA0030000,
                       uart=0xA0080000,
                       brom_payload_addr=0x100A00,
                       da_payload_addr=0x200000,
                       # no gcpu_base
                       # no sej_base
                       # no dxcc
                       # no cqdma_base
                       # no ap_dma_mem
                       # blacklist
                       damode=damodes.DEFAULT,
                       dacode=0x6261,
                       name="MT6261"),
    0x633: chipconfig(  # var1
        watchdog=0x10007000,
        uart=0x11002000,
        brom_payload_addr=0x100A00,  # todo: check
        da_payload_addr=0x200000,
        gcpu_base=0x1020D000,
        sej_base=0x1000A000,
        # no dxcc
        cqdma_base=0x1020ac00,
        ap_dma_mem=0x11000000 + 0x1A0,  # AP_P_DMA_I2C_RX_MEM_ADDR
        damode=damodes.XFLASH,
        dacode=0x6570,
        name="MT6570"),
    0x6516: chipconfig(  # var1
        watchdog=0x10003000,
        uart=0x10023000,
        da_payload_addr=0x200000,  # todo: check
        # gcpu_base
        sej_base=0x1002D000,
        # no dxcc
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.DEFAULT,
        dacode=0x6516,
        name="MT6516"),
    0x6571: chipconfig(  # var1
        watchdog=0x10007400,
        # uart
        da_payload_addr=0x2008000,
        # gcpu_base
        # sej_base
        # no dxcc
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.DEFAULT,  #
        dacode=0x6571,
        name="MT6571"),
    0x6572: chipconfig(var1=0xA,
                       watchdog=0x10007000,
                       uart=0x11005000,
                       brom_payload_addr=0x10036A0,
                       da_payload_addr=0x2007000,
                       # gcpu_base
                       # sej_base
                       # no dxcc
                       # cqdma_base
                       ap_dma_mem=0x11000000 + 0x19C,  # AP_P_DMA_I2C_1_MEM_ADDR
                       # blacklist
                       damode=damodes.DEFAULT,  #
                       dacode=0x6572,
                       name="MT6572"),
    0x6573: chipconfig(  # var1
        watchdog=0x220,
        # uart
        da_payload_addr=0x90005000,
        # gcpu_base
        # sej_base
        # dxcc_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.DEFAULT,
        dacode=0x6573,
        name="MT6573"),
    0x6575: chipconfig(  # var1
        watchdog=0xC0000000,
        # uart
        da_payload_addr=0xc2000000,
        # gcpu_base
        # sej_base
        # dxcc_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        ap_dma_mem=0xC100119C,
        sej_base=0xC101A000,
        damode=damodes.DEFAULT,  #
        dacode=0x6575,
        name="MT6575/77"),
    0x6577: chipconfig(  # var1
        watchdog=0xC0000000,  # fixme
        uart=0xC1009000,
        da_payload_addr=0xc2000000,
        # gcpu_base
        sej_base=0xC101A000,
        # dxcc_base
        # cqdma_base
        ap_dma_mem=0xC100119C,
        # blacklist
        damode=damodes.DEFAULT,  #
        dacode=0x6577,
        name="MT6577"),
    0x6580: chipconfig(  # var1
        watchdog=0x10007000,
        uart=0x11005000,
        brom_payload_addr=0x100A00,
        da_payload_addr=0x200000,
        # no gcpu_base
        sej_base=0x1000A000,
        # dxcc_base
        cqdma_base=0x1020AC00,
        ap_dma_mem=0x11000000 + 0x1A0,  # AP_P_DMA_I2C_1_RX_MEM_ADDR
        blacklist=[(0x102764, 0x0)],
        damode=damodes.DEFAULT,
        dacode=0x6580,
        name="MT6580"),
    0x6582: chipconfig(var1=0xA, #confirmed
                       watchdog=0x10007000,
                       uart=0x11002000,
                       brom_payload_addr=0x100A00,
                       da_payload_addr=0x200000,
                       pl_payload_addr=0x80001000,
                       gcpu_base=0x1101B000,
                       sej_base=0x1000A000,
                       # dxcc_base
                       # no cqdma_base
                       ap_dma_mem=0x11000000 + 0x320,  # AP_DMA_I2C_0_RX_MEM_ADDR
                       blacklist=[(0x102788, 0x0)],
                       damode=damodes.DEFAULT,  #
                       dacode=0x6582,
                       name="MT6582/MT6574"),
    0x6588: chipconfig(  # var1
        watchdog=0x10000000,
        # uart
        # brom_payload_addr
        # da_payload_addr
        # gcpu_base
        # sej_base
        # dxcc_base
        # cqdma_base
        ap_dma_mem=0x11000000 + 0x1A0,
        # blacklist
        damode=damodes.DEFAULT,
        dacode=0x6588,
        name="MT6588"),
    0x6583: chipconfig(  # var1
        watchdog=0x10000000,  # fixme
        uart=0x11006000,
        brom_payload_addr=0x100A00,
        da_payload_addr=0x200000,
        gcpu_base=0x10210000,
        sej_base=0x1000A000,
        # no dxcc
        cqdma_base=0x10212000,  # This chip might not support cqdma
        ap_dma_mem=0x11000000 + 0x320,  # AP_DMA_I2C_0_RX_MEM_ADDR
        damode=damodes.DEFAULT,
        dacode=0x6589,
        name="MT6589"),
    0x6592: chipconfig(  # var1
        watchdog=0x10007000,
        # uart
        # brom_payload_addr
        da_payload_addr=0x110000,
        # gcpu_base
        # sej_base
        # dxcc_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        dacode=0x6592,
        damode=damodes.DEFAULT,  #
        name="MT6592"),
    0x6595: chipconfig(  # var1
        watchdog=0x10007000,
        # uart
        # brom_payload_addr
        da_payload_addr=0x110000,
        # gcpu_base
        sej_base=0x1000A000,
        # dxcc_base
        # cqdma_base
        ap_dma_mem=0x11000000 + 0x1A0,
        # blacklist
        dacode=0x6595,
        damode=damodes.DEFAULT,  #
        name="MT6595"),
    0x321: chipconfig(var1=0x28,
                      watchdog=0x10212000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      pl_payload_addr=0x40200000,
                      gcpu_base=0x10216000,  # mt6735, 6737, 6753, 6735m
                      sej_base=0x10008000,
                      # no dxcc
                      cqdma_base=0x10217C00,
                      ap_dma_mem=0x11000000 + 0x1A0,  # AP_DMA_I2C_O_RX_MEM_ADDR
                      blacklist=[(0x00102760, 0x0), (0x00105704, 0x0)],
                      damode=damodes.DEFAULT,  #
                      dacode=0x6735,
                      name="MT6735/T"),
    0x335: chipconfig(var1=0x28,  # confirmed
                      watchdog=0x10212000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      pl_payload_addr=0x40200000,
                      gcpu_base=0x10216000,  # mt6735, 6737, 6753, 6735m
                      sej_base=0x10008000,
                      # no dxcc
                      cqdma_base=0x10217C00,
                      ap_dma_mem=0x11000000 + 0x1A0,  # AP_DMA_I2C_O_RX_MEM_ADDR
                      blacklist=[(0x00102760, 0x0), (0x00105704, 0x0)],
                      damode=damodes.DEFAULT,  #
                      dacode=0x6735,
                      name="MT6737M"),
    # MT6738
    0x699: chipconfig(var1=0xB4,
                      watchdog=0x10007000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      pl_payload_addr=0x40200000,
                      gcpu_base=0x10050000,
                      sej_base=0x1000A000,  # hacc
                      dxcc_base=0x10210000,
                      cqdma_base=0x10212000,
                      ap_dma_mem=0x11000000 + 0x1a0,  # AP_DMA_I2C_1_RX_MEM_ADDR
                      blacklist=[(0x10282C, 0x0)],
                      damode=damodes.XFLASH,
                      dacode=0x6739,
                      name="MT6739/MT6731"),
    0x6752: chipconfig(  # var1
        watchdog=0x10007000,
        uart=0x11002000,
        brom_payload_addr=0x100A00,
        da_payload_addr=0x110000,
        pl_payload_addr=0x40200000,
        gcpu_base=0x10210000,
        sej_base=0x1000A000,  # hacc
        # no dxcc
        cqdma_base=0x10212C00,
        ap_dma_mem=0x11000000 + 0x1A0,  # AP_DMA_I2C_0_RX_MEM_ADDR
        # blacklist
        damode=damodes.DEFAULT,  #
        dacode=0x6752,
        name="MT6752"),
    0x337: chipconfig(var1=0x28,  # confirmed
        watchdog=0x10212000,
        uart=0x11002000,
        brom_payload_addr=0x100A00,
        da_payload_addr=0x200000,
        pl_payload_addr=0x40200000,
        gcpu_base=0x10216000,
        sej_base=0x10008000,
        # no dxcc
        cqdma_base=0x10217C00,
        ap_dma_mem=0x11000000 + 0x1A0,  # AP_DMA_I2C_0_RX_MEM_ADDR
        blacklist=[(0x00102760, 0x0), (0x00105704, 0x0)],
        damode=damodes.DEFAULT,  #
        dacode=0x6753,
        name="MT6753"),
    0x571: chipconfig(  # var1
        watchdog=0x10007000,
        # uart
        # brom_payload_addr
        # da_payload_addr
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.DEFAULT,  #
        dacode=0x0571,
        name="MT0571"),
    0x598: chipconfig(  # var1
        watchdog=0x10211000,
        uart=0x11020000,
        brom_payload_addr=0x100A00,  # todo:check
        da_payload_addr=0x200000,  # todo:check
        gcpu_base=0x10224000,
        sej_base=0x1000A000,
        cqdma_base=0x10212c00,
        ap_dma_mem=0x11000000 + 0x1A0,
        # blacklist
        damode=damodes.DEFAULT,
        dacode=0x0598,
        name="ELBRUS/MT0598"),
    0x992: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        # da_payload_addr
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.XFLASH,
        dacode=0x0992,
        name="MT0992"),
    0x601: chipconfig(var1=0xA,
                      watchdog=0x10007000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      gcpu_base=0x10210000,
                      sej_base=0x1000A000,  # hacc
                      cqdma_base=0x10212C00,
                      ap_dma_mem=0x11000000 + 0x1A0,  # AP_DMA_I2C_1_RX_MEM_ADDR
                      # blacklist
                      damode=damodes.XFLASH,
                      dacode=0x6750,
                      name="MT6750"),
    0x326: chipconfig(var1=0xA,
                      watchdog=0x10007000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      pl_payload_addr=0x40200000,
                      gcpu_base=0x10210000,
                      sej_base=0x1000A000,  # hacc
                      cqdma_base=0x10212C00,
                      ap_dma_mem=0x11000000 + 0x1A0,  # AP_DMA_I2C_1_RX_MEM_ADDR
                      blacklist=[(0x10276C, 0x0)],
                      damode=damodes.XFLASH,
                      dacode=0x6755,
                      name="MT6755/M/T/S",
                      description="Helio P10/P15/P18"),
    0x551: chipconfig(var1=0xA,
                      watchdog=0x10007000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      gcpu_base=0x10210000,
                      sej_base=0x1000A000,
                      cqdma_base=0x10212C00,
                      ap_dma_mem=0x11000000 + 0x1A0,  # AP_DMA_I2C_1_RX_MEM_ADDR
                      blacklist=[(0x102774, 0x0)],
                      damode=damodes.XFLASH,
                      dacode=0x6757,
                      name="MT6757/MT6757D",
                      description="Helio P20"),
    0x688: chipconfig(  # var1
        watchdog=0x10210000,
        uart=0x11020000,
        brom_payload_addr=0x100A00,  # todo
        da_payload_addr=0x200000,
        gcpu_base=0x10050000,
        sej_base=0x10080000,  # hacc
        # no dxcc
        cqdma_base=0x10200000,
        ap_dma_mem=0x11000000 + 0x1A0,
        # blacklist
        damode=damodes.XFLASH,
        dacode=0x6758,
        name="MT6758",
        description="Helio P30"),
    0x507: chipconfig(  # var1
        watchdog=0x10210000,
        uart=0x11020000,
        brom_payload_addr=0x100A00,  # todo
        da_payload_addr=0x200000,
        gcpu_base=0x10210000,
        # sej_base
        # cqdma_base
        ap_dma_mem=0x1030000 + 0x1A0,  # todo
        # blacklist
        damode=damodes.DEFAULT,
        dacode=0x6759,  # todo
        name="MT6759"),
    0x717: chipconfig(var1=0x25,
                      watchdog=0x10007000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      gcpu_base=0x10050000,
                      sej_base=0x1000A000,  # hacc
                      dxcc_base=0x10210000,
                      cqdma_base=0x10212000,
                      ap_dma_mem=0x11000a80 + 0x1a0,  # AP_DMA_I2C_CH0_RX_MEM_ADDR
                      blacklist=[(0x102828, 0x0)],
                      damode=damodes.XFLASH,
                      dacode=0x6761,
                      name="MT6761/MT6762/MT3369",
                      description="Helio A20/P22/A22/A25/G25"),
    0x690: chipconfig(var1=0x7F,
                      watchdog=0x10007000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      gcpu_base=0x10050000,
                      dxcc_base=0x10210000,
                      sej_base=0x1000A000,  # hacc
                      cqdma_base=0x10212000,
                      ap_dma_mem=0x11000a80 + 0x1a0,
                      blacklist=[(0x102834, 0x0)],
                      damode=damodes.XFLASH,
                      dacode=0x6763,
                      name="MT6763",
                      description="Helio P23"),
    0x766: chipconfig(var1=0x25, #confirmed
                      watchdog=0x10007000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      pl_payload_addr=0x40200000,
                      gcpu_base=0x10050000, # not confirmed
                      sej_base=0x1000a000,  # hacc
                      dxcc_base=0x10210000,
                      cqdma_base=0x10212000,
                      ap_dma_mem=0x11000000 + 0x1a0,  # AP_DMA_I2C2_CH0_RX_MEM_ADDR
                      blacklist=[(0x102828, 0x0)],
                      damode=damodes.XFLASH,
                      dacode=0x6765,
                      name="MT6765",
                      description="Helio P35/G35"),
    0x707: chipconfig(var1=0x25,  # todo
                      watchdog=0x10007000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      gcpu_base=0x10050000,
                      sej_base=0x1000A000,  # hacc
                      dxcc_base=0x10210000,
                      cqdma_base=0x10212000,
                      ap_dma_mem=0x11000000 + 0x1A0,
                      blacklist=[(0x10282C, 0x0)],
                      damode=damodes.XFLASH,
                      dacode=0x6768,
                      name="MT6768",
                      description="Helio P65/G85"),
    0x788: chipconfig(var1=0xA,
                      watchdog=0x10007000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      gcpu_base=0x10050000,
                      sej_base=0x1000A000,  # hacc
                      dxcc_base=0x10210000,  # dxcc_sec
                      cqdma_base=0x10212000,
                      ap_dma_mem=0x11000000 + 0x158,  # AP_DMA_I2C_1_RX_MEM_ADDR
                      blacklist=[(0x00102834, 0x0)],
                      damode=damodes.XFLASH,
                      dacode=0x6771,
                      name="MT6771/MT8385/MT8183/MT8666",
                      description="Helio P60/P70/G80"),
    #blacklist=[(0x00102830, 0x00200008),  # Static permission table pointer
    #           (0x00102834, 2),  # Static permission table entry count
    #           (0x00200000, 0x00000000),  # Memory region minimum address
    #           (0x00200004, 0xfffffffc),  # Memory region maximum address
    #           (0x00200008, 0x00000200),  # Memory read command bitmask
    #           (0x0020000c, 0x00200000),  # Memory region array pointer
    #           (0x00200010, 0x00000001),  # Memory region array length
    #           (0x00200014, 0x00000400),  # Memory write command bitmask
    #           (0x00200018, 0x00200000),  # Memory region array pointer
    #           (0x0020001c, 0x00000001),  # Memory region array length
    #           (0x00106A60, 0)],  # Dynamic permission table entry count?),
    0x725: chipconfig(var1=0xA, #confirmed
        watchdog=0x10007000,
        uart=0x11002000,
        brom_payload_addr=0x100A00,
        da_payload_addr=0x200000,
        gcpu_base=0x10050000,
        sej_base=0x1000a000,  # hacc
        dxcc_base=0x10210000,
        cqdma_base=0x10212000,
        ap_dma_mem=0x11000000 + 0x158,
        blacklist=[(0x102838, 0x0)],
        damode=damodes.XFLASH,
        dacode=0x6779,
        name="MT6779",
        description="Helio P90"),
    0x813: chipconfig(  # var1=0xA, #todo
        watchdog=0x10007000,
        uart=0x11002000,
        brom_payload_addr=0x100A00,
        da_payload_addr=0x200000,
        gcpu_base=0x10050000,
        sej_base=0x1000A000,  # hacc
        dxcc_base=0x10210000,
        cqdma_base=0x10212000,
        ap_dma_mem=0x11000000 + 0x158,
        blacklist=[(0x102838, 0x0)],
        damode=damodes.XFLASH,
        dacode=0x6785,
        name="MT6785",
        description="Helio G90"),
    0x6795: chipconfig(
        var1=0xA, #confirmed
        watchdog=0x10007000,
        uart=0x11002000,
        brom_payload_addr=0x100A00,
        da_payload_addr=0x110000,
        gcpu_base=0x10210000,
        sej_base=0x1000A000,  # hacc
        # no dxcc
        cqdma_base=0x10212c00,
        ap_dma_mem=0x11000000 + 0x1A0,
        blacklist=[(0x102764, 0x0)],
        damode=damodes.DEFAULT,  #
        dacode=0x6795,
        name="MT6795",
        description="Helio X10"),
    0x279: chipconfig(var1=0xA,  # confirmed
                      watchdog=0x10007000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      gcpu_base=0x10210000,
                      # no dxcc
                      sej_base=0x1000A000,  # hacc
                      cqdma_base=0x10212C00,
                      ap_dma_mem=0x11000000 + 0x1A0,  # AP_DMA_I2C_1_RX_MEM_ADDR
                      blacklist=[(0x0010276C, 0x0), (0x00105704, 0x0)],
                      damode=damodes.XFLASH,
                      dacode=0x6797,
                      name="MT6797"),
    0x562: chipconfig(var1=0xA,  # confirmed
                      watchdog=0x10211000,
                      uart=0x11020000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      gcpu_base=0x10210000,
                      cqdma_base=0x11B30000,
                      ap_dma_mem=0x11000000 + 0x1A0,  # AP_DMA_I2C_2_RX_MEM_ADDR
                      # no dxcc
                      sej_base=0x1000A000,
                      blacklist=[(0x00102870, 0x0)],
                      damode=damodes.XFLASH,
                      dacode=0x6799,
                      name="MT6799"),
    0x989: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        da_payload_addr=0x200000,
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.XFLASH,
        dacode=0x6833,
        name="MT6833"),
    0x996: chipconfig(  # var1
        watchdog=0x10007000,
        uart=0x11002000,
        brom_payload_addr=0x100A00,
        da_payload_addr=0x200000,
        gcpu_base=0x10050000,
        dxcc_base=0x10210000,
        cqdma_base=0x10212000,
        sej_base=0x1000a000,  # hacc
        ap_dma_mem=0x11000000 + 0x1A0,
        # blacklist
        damode=damodes.XFLASH,
        dacode=0x6853,
        name="MT6853"),
    0x886: chipconfig(var1=0xA,
                      watchdog=0x10007000,
                      uart=0x11002000,
                      brom_payload_addr=0x100A00,
                      da_payload_addr=0x200000,
                      gcpu_base=0x10050000,
                      dxcc_base=0x10210000,
                      sej_base=0x1000a000,  # hacc
                      cqdma_base=0x10212000,
                      ap_dma_mem=0x11000000 + 0x1A0,
                      blacklist=[(0x10284C, 0x0)],
                      damode=damodes.XFLASH,
                      dacode=0x6873,
                      name="MT6873",
                      description="Dimensity 800 5G"),
    0x959: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        # da_payload_addr
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.XFLASH,
        dacode=0x6877,  # todo
        name="MT6877"),
    0x816: chipconfig(
        var1=0xA, # confirmed
        watchdog=0x10007000,
        uart=0x11002000,
        brom_payload_addr=0x100A00,
        da_payload_addr=0x200000,
        gcpu_base=0x10050000,
        dxcc_base=0x10210000,
        sej_base=0x1000a000,  # hacc
        cqdma_base=0x10212000,
        ap_dma_mem=0x11000a80 + 0x1a0,  # todo check
        blacklist=[(0x102848, 0x0)],
        damode=damodes.XFLASH,
        dacode=0x6885,
        name="MT6885"),
    0x950: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        da_payload_addr=0x200000,  # todo
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.XFLASH,
        dacode=0x6893,
        name="MT6893"),
    0x7623: chipconfig(  # var1
        watchdog=0x10007000,
        uart=0x11002000,
        brom_payload_addr=0x100A00,
        da_payload_addr=0x200000,
        gcpu_base=0x1101B000,
        sej_base=0x1000A000,
        # cqdma_base
        ap_dma_mem=0x11000000 + 0x1A0,
        # blacklist
        damode=damodes.DEFAULT,
        dacode=0x8590,
        name="MT7623"),
    0x7683: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        # da_payload_addr
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.DEFAULT,
        dacode=0x8590,
        name="MT7683"),
    0x8110: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        # da_payload_addr
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.XFLASH,
        dacode=0x8110,
        name="MT8110"),
    0x8127: chipconfig(var1=0xA,
                       watchdog=0x10007000,
                       uart=0x11002000,
                       brom_payload_addr=0x100A00,
                       da_payload_addr=0x200000,
                       gcpu_base=0x11010000,
                       sej_base=0x1000A000,
                       # no cqdma_base
                       ap_dma_mem=0x11000000 + 0x1A0,
                       blacklist=[(0x102870, 0x0)],
                       damode=damodes.DEFAULT,  #
                       dacode=0x8127,
                       name="MT8127/MT3367"),  # ford,austin,tank #mhmm wdt, nochmal checken
    0x8135: chipconfig(  # var1
        watchdog=0x10000000,
        # uart
        # brom_payload_addr
        # da_payload_addr
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.DEFAULT,  #
        dacode=0x8135,
        name="MT8135"),
    0x8163: chipconfig(var1=0xB1,
                       watchdog=0x10007000,
                       uart=0x11002000,
                       brom_payload_addr=0x100A00,
                       da_payload_addr=0x200000,
                       gcpu_base=0x10210000,
                       sej_base=0x1000A000,
                       # no dxcc
                       cqdma_base=0x10212C00,
                       ap_dma_mem=0x11000000 + 0x1A0,
                       blacklist=[(0x102868, 0x0), (0x001072DC, 0x0)],
                       damode=damodes.DEFAULT,  #
                       dacode=0x8163,
                       name="MT8163"),  # douglas, karnak
    0x8167: chipconfig(  # var1
        watchdog=0x10007000,
        uart=0x11005000,
        brom_payload_addr=0x100A00,
        da_payload_addr=0x200000,
        gcpu_base=0x1020D000,
        sej_base=0x1000A000,
        # no dxcc
        cqdma_base=0x10212C00,
        ap_dma_mem=0x11000000 + 0x1A0,
        # blacklist
        damode=damodes.XFLASH,
        dacode=0x8167,
        name="MT8167/MT8516/MT8362"),
    0x8168: chipconfig(  # var1
        watchdog=0x10007000,
        uart=0x11002000,
        brom_payload_addr=0x100A00,
        da_payload_addr=0x200000,  # todo
        # gcpu_base
        # sej_base
        # cqdma_base
        ap_dma_mem=0x11000000 + 0x1A0,
        # blacklist
        damode=damodes.XFLASH,
        dacode=0x8168,
        name="MT8168"),
    0x8172: chipconfig(var1=0xA,  # todo
                       watchdog=0x10007000,
                       uart=0x11002000,
                       brom_payload_addr=0x120A00,
                       da_payload_addr=0xc0000,
                       # gcpu_base
                       # sej_base
                       # cqdma_base
                       ap_dma_mem=0x11000000 + 0x1A0,
                       blacklist=[(0x122774, 0x0)],
                       damode=damodes.DEFAULT,  #
                       dacode=0x8173,
                       name="MT8173"),  # sloane, suez
    0x8176: chipconfig(  # var1
        watchdog=0x10212c00,
        # uart
        # brom_payload_addr
        # da_payload_addr
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        dacode=0x8173,
        damode=damodes.DEFAULT,  #
        name="MT8176"),
    0x930: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        da_payload_addr=0x200000,
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        dacode=0x8195,
        damode=damodes.XFLASH,
        name="MT8195"),
    0x8512: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        da_payload_addr=0x110000,
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        dacode=0x8512,
        damode=damodes.XFLASH,
        name="MT8512"),
    0x8518: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        da_payload_addr=0x200000,
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        dacode=0x8518,
        damode=damodes.XFLASH,
        name="MT8518"),
    0x8590: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        da_payload_addr=0x200000,
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        dacode=0x8590,
        damode=damodes.DEFAULT,  #
        name="MT8590/MT8521"),
    0x8695: chipconfig(var1=0xA, #confirmed
                       watchdog=0x10007000,
                       uart=0x11002000,
                       brom_payload_addr=0x100A00,
                       da_payload_addr=0x200000,
                       pl_payload_addr=0x40001000,
                       # gcpu_base
                       # sej_base
                       # cqdma_base
                       ap_dma_mem=0x11000280 + 0x1A0,
                       blacklist=[(0x103048, 0x0)],
                       damode=damodes.XFLASH,
                       dacode=0x8695,
                       name="MT8695"),
    0x908: chipconfig(  # var1
        # watchdog
        # uart
        # brom_payload_addr
        da_payload_addr=0x200000,
        # gcpu_base
        # sej_base
        # cqdma_base
        # ap_dma_mem
        # blacklist
        damode=damodes.XFLASH,
        dacode=0x8696,
        name="MT8696"),
}


# 6570, 6595, 6758, 6763, 6779, 6797, 6853, 8167, 8168, 8195, 8512, 8518, 8590, 8696
# MT6732M
# MT6738
# MT6738
# "mt6763T":"Helio P23"
# "mt6779":"Helio P90"),
# "mt6779/CV": "Helio P90/P95"),
# "mt6799": "Helio X30"),
# "mt6797": "Helio X20/X25"),
# "mt6797D":"Helio X23/X27/X30"),
# "mt6595":
# mt8192,mt8195
# mt6885 Dimensity 1000L
# MT6893 Dimensity 1200
# mt6833 Dimensity 700
# mt6853 Dimensity 720
# G95
# G80 (vivo y20g)
# G70 (Infinix Hot 10)

class Mtk_Config(metaclass=LogBase):
    def __init__(self, mtk, hwcode, loglevel=logging.INFO):
        self.bmtflag = None
        self.bmtblockcount = None
        self.bmtpartsize = None
        self.packetsizeread = 0x400
        self.flashinfo = None
        self.flashsize = 0
        self.readsize = 0
        self.sparesize = 16
        self.da = None
        self.gcpu = None
        self.pagesize = 512
        self.SECTOR_SIZE_IN_BYTES = 4096  # fixme
        self.baudrate = 115200
        self.flash = "emmc"
        self.cpu = ""
        self.hwcode = hwcode
        self.meid = None
        self.target_config = None
        self.mtk = mtk
        self.chipconfig = chipconfig()
        if loglevel == logging.DEBUG:
            logfilename = "log.txt"
            if os.path.exists(logfilename):
                os.remove(logfilename)
            fh = logging.FileHandler(logfilename)
            self.__logger.addHandler(fh)
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger.setLevel(logging.INFO)

    def default_values(self, hwcode):
        if self.chipconfig.var1 is None:
            self.chipconfig.var1 = 0xA
        if self.chipconfig.watchdog is None:
            self.chipconfig.watchdog = 0x10007000
        if self.chipconfig.uart is None:
            self.chipconfig.uart = 0x11002000
        if self.chipconfig.brom_payload_addr is None:
            self.chipconfig.brom_payload_addr = 0x100A00
        if self.chipconfig.da_payload_addr is None:
            self.chipconfig.da_payload_addr = 0x200000
        if self.chipconfig.cqdma_base is None:
            self.chipconfig.cqdma_base = None
        if self.chipconfig.gcpu_base is None:
            self.chipconfig.gcpu_base = None
        if self.chipconfig.sej_base is None:
            self.chipconfig.sej_base = 0x10008000
        if self.chipconfig.dacode is None:
            self.chipconfig.dacode = hwcode
        if self.chipconfig.ap_dma_mem is None:
            self.chipconfig.ap_dma_mem = 0x11000000 + 0x1A0
        if self.chipconfig.damode is None:
            self.chipconfig.damode = damodes.DEFAULT
        if self.chipconfig.dxcc_base is None:
            self.chipconfig.dxcc_base = 0x10210000

    def init_hwcode(self, hwcode):
        if hwcode in hwconfig:
            self.chipconfig = hwconfig[hwcode]
        else:
            self.chipconfig = chipconfig()
        self.default_values(hwcode)

    def get_watchdog_addr(self):
        wdt = self.chipconfig.watchdog
        if wdt != 0:
            if wdt == 0x10007000:
                return [wdt, 0x22000064]
            elif wdt == 0x10212000:
                return [wdt, 0x22000000]
            elif wdt == 0x10211000:
                return [wdt, 0x22000064]
            elif wdt == 0x10007400:
                return [wdt, 0x22000000]
            elif wdt == 0xC0000000:
                return [wdt, 0x0]
            elif wdt == 0x2200:
                if self.hwcode == 0x6276 or self.hwcode == 0x8163:
                    return [wdt, 0x610C0000]
                elif self.hwcode == 0x6251 or self.hwcode == 0x6516:
                    return [wdt, 0x80030000]
                elif self.hwcode == 0x6255:
                    return [wdt, 0x701E0000]
                else:
                    return [wdt, 0x70025000]
            else:
                return [wdt, 0x22000064]

    def bmtsettings(self, hwcode):
        bmtflag = 1
        bmtblockcount = 0
        bmtpartsize = 0
        if hwcode in [0x6592, 0x6582, 0x8127, 0x6571]:
            if self.flash == "emmc":
                bmtflag = 1
                bmtblockcount = 0xA8
                bmtpartsize = 0x1500000
        elif hwcode in [0x6570, 0x8167, 0x6580, 0x6735, 0x6753, 0x6755, 0x6752, 0x6595, 0x6795, 0x6797, 0x8163]:
            bmtflag = 1
            bmtpartsize = 0
        elif hwcode in [0x6571]:
            if self.flash == "nand":
                bmtflag = 0
                bmtblockcount = 0x38
                bmtpartsize = 0xE00000
            elif self.flash == "emmc":
                bmtflag = 1
                bmtblockcount = 0xA8
                bmtpartsize = 0x1500000
        elif hwcode in [0x6575]:
            if self.flash == "nand":
                bmtflag = 0
                bmtblockcount = 0x50
            elif self.flash == "emmc":
                bmtflag = 1
                bmtblockcount = 0xA8
                bmtpartsize = 0x1500000
        elif hwcode in [0x6572]:
            if self.flash == "nand":
                bmtflag = 0
                bmtpartsize = 0xA00000
                bmtblockcount = 0x50
            elif self.flash == "emmc":
                bmtflag = 1
                bmtblockcount = 0xA8
                bmtpartsize = 0x0
        elif hwcode in [0x6577, 0x6583, 0x6589]:
            if self.flash == "nand":
                bmtflag = 0
                bmtpartsize = 0xA00000
                bmtblockcount = 0xA8
        self.bmtflag = bmtflag
        self.bmtblockcount = bmtblockcount
        self.bmtpartsize = bmtpartsize
