# mtkclient
Just some mtk tool. The small brother (<1%) of my upcoming "mtk exploit platform tools". For linux, a patched kernel is needed (see Setup folder).
For windows, you need to install zadig driver.

# Installation
`` 
pip3 -r install requirements.txt 
``

# Usage

Dump bootrom
`` 
./mtk.py dumpbrom
`` 

Disable security
`` 
./mtk.py payload
`` 

Run stage2 in bootrom
`` 
./mtk.py stage
`` 

Run stage2 in preloader
`` 
./mtk.py plstage
`` 

Crash preloader and enter bootrom
`` 
./mtk.py crash
`` 


Once it's running, boot into brom mode by powering off device, press and hold either
vol up + power or vol down + power and connect the phone. Once detected by the tool,
release the buttons.

Usage of https://github.com/amonet-kamakiri/fireiso/releases/tag/v2.0.0 FireIso Live DVD
is strongly recommended
