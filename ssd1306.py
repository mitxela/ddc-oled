
# composite cursor after dithering
# args to set device, contrast,  wrapper to launch?
# clock script?

dev = "/dev/i2c-3"
contrast = 0x0f

import io, fcntl
I2C_SLAVE=0x0703 # from i2c-dev.h
i2caddr = 0x3c

bus = io.open(dev, "wb", buffering=0)
fcntl.ioctl(bus, I2C_SLAVE, i2caddr)

def ssd1306_cmd(cmd):
    bus.write(bytearray([0]+cmd))

def ssd1306_data(data):
    chunk = 256
    for i in range(0, len(data), chunk):
        bus.write(bytearray([0x40]+data[i:i+chunk]))


# ssd1306 init
ssd1306_cmd([
0xae, # Display off (reset)
0xd5, # Set display clock div
0x80, #     Suggested ratio (reset: 0x80)
0xa8, # Set mux ratio
0x3f, #     height-1 (reset: 63)
0xd3, # Set display offset
0x00, #     No offset (reset: 0)
0x40, # Set startline = 0 (0x40 | 0x00) (reset: 0x40)

0x8d, # Charge pump - documented separately
0x14, #     charge pump enable

0x20, # Memory mode
0x00, #     Horizontal addressing mode (reset: page address mode)
0xa1, # Segment remap: col 127 is mapped to SEG0

0xc8, # com scan direction remapped (reset: 0xc0)

0xda, # Set com pins
0x12, #     reset: 0x12

0x81, # Set contrast
contrast, # 0xcf for internal vcc (reset: 0x7f)

0xd9, # Set precharge period
0xf1, #     for internal vcc (reset: 0x22)
0xdb, # Set vcomh deselect level
0x40, #     undocumented (reset: 0x20)

0xa4, # Resume entire display on (reset)
0xa6, # Normal display (reset)
0xaf]) # Display on


from Xlib import display, X
from PIL import Image
import numpy as np

d = display.Display()
root = d.screen().root

from pyxcursor import Xcursor
cursor = Xcursor()

x = 1920
y = 0
w = 128
h = 64

cb = 10 # cursor boundary

def getFrameAsByteList():
    raw = root.get_image(x,y,w,h, X.ZPixmap, 0xffffffff)
    simg = Image.frombytes("RGB", (w, h), raw.data, "raw", "BGRX")

    pointer = root.query_pointer()
    px, py = pointer.root_x, pointer.root_y
    if px >= x-cb and px<=x+w+cb and py >= y-cb and py < y+h+cb:
        iarray, xhot, yhot = cursor.getCursorImageArrayFast()
        cimg = Image.fromarray(iarray)
        simg.paste(cimg, (px-x-xhot,py-y-yhot), cimg) 
    
    b = simg.convert("1", dither=0).rotate(-90,expand=True).tobytes()
    r = np.frombuffer(b, np.uint8).reshape(w,h//8)
    r = np.transpose(r)
    r = np.flip(r, 0)

    return list(r.tobytes())

# There is no way to simply set the pointer, we have to reconfigure the draw area
# There is an eight? byte cost to setting the draw area, plus setting it back afterwards

def setDrawArea(col,page):
    ssd1306_cmd([0x21, col, 127, 0x22, page, 7])

oldbuffer = getFrameAsByteList()
setDrawArea(0,0)
ssd1306_data(oldbuffer)

import time

cost = 8

while True:
    newbuffer = getFrameAsByteList()
    changed = list(map(lambda a,b: int(a!=b), newbuffer, oldbuffer))

    if sum(changed)==0:
        time.sleep(0.016)
        continue

    transactions = []
    i=0
    while i<1024:
        if changed[i]:
            # look for the next group of unchanged bytes larger than cost
            start = i
            while sum(changed[i:i+cost])!=0 and i<1024:
                i+=1
            end=i-1
            # at this point, we need to worry about if the transaction crosses a page boundary
            # if start_col != 0 and start_page != end_page, split transaction
            if start%128 != 0 and start//128 != end//128:
                split_point = ((start//128)+1)*128
                transactions.append((start, split_point-1))
                transactions.append((split_point, end))
            else:
                transactions.append((start, end))
        else:
            i+=1
    
    # future optimization: transactions on adjacent pages with similar start and end col can be combined

    for start, end in transactions:
        setDrawArea( start%128, start//128 )
        ssd1306_data( newbuffer[start:end+1] )

    oldbuffer = newbuffer


