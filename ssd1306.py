import io, fcntl

dev = "/dev/i2c-3"
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
ssd1306_cmd([0xae]) # Display off (reset)
ssd1306_cmd([0xd5]) # Set display clock div
ssd1306_cmd([0x80]) #     Suggested ratio (reset: 0x80)
ssd1306_cmd([0xa8]) # Set mux ratio
ssd1306_cmd([0x3f]) #     height-1 (reset: 63)
ssd1306_cmd([0xd3]) # Set display offset
ssd1306_cmd([0x00]) #     No offset (reset: 0)
ssd1306_cmd([0x40]) # Set startline = 0 (0x40 | 0x00) (reset: 0x40)

ssd1306_cmd([0x8d]) # Charge pump - documented separately
ssd1306_cmd([0x14]) #     charge pump enable

ssd1306_cmd([0x20]) # Memory mode
ssd1306_cmd([0x00]) #     Horizontal addressing mode (reset: page address mode)
ssd1306_cmd([0xa1]) # Segment remap: col 127 is mapped to SEG0

ssd1306_cmd([0xc8]) # com scan direction remapped (reset: 0xc0)

ssd1306_cmd([0xda]) # Set com pins
ssd1306_cmd([0x12]) #     reset: 0x12

ssd1306_cmd([0x81]) # Set contrast
ssd1306_cmd([0xcf]) #     Contrast for internal vcc (reset: 0x7f)

ssd1306_cmd([0xd9]) # Set precharge period
ssd1306_cmd([0xf1]) #     for internal vcc (reset: 0x22)
ssd1306_cmd([0xdb]) # Set vcomh deselect level
ssd1306_cmd([0x40]) #     undocumented (reset: 0x20)

ssd1306_cmd([0xa4]) # Resume entire display on (reset)
ssd1306_cmd([0xa6]) # Normal display (reset)
ssd1306_cmd([0xaf]) # Display on

ssd1306_cmd([0x21]) #Column address
ssd1306_cmd([0x00]) #Start column 0
ssd1306_cmd([0x7F]) #End column 127
ssd1306_cmd([0x22]) #Page address
ssd1306_cmd([0x00]) #Start page 0
ssd1306_cmd([0x07]) #End page 7



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

def getFrameAsByteList():
    raw = root.get_image(x,y,w,h, X.ZPixmap, 0xffffffff)
    simg = Image.frombytes("RGB", (w, h), raw.data, "raw", "BGRX")

    pointer = root.query_pointer()
    px, py = pointer.root_x, pointer.root_y
    if px > x and py < h:
        iarray, xhot, yhot = cursor.getCursorImageArrayFast()
        cimg = Image.fromarray(iarray)
        simg.paste(cimg, (px-x-xhot,py-y-yhot), cimg) 
    
    b = simg.convert("1",dither=0).rotate(-90,expand=True).tobytes()
    r = np.frombuffer(b, np.uint8).reshape(w,h//8)
    r = np.transpose(r)
    r = np.flip(r, 0)

    return list(r.tobytes())


oldbuffer = getFrameAsByteList()
ssd1306_data(oldbuffer)

#ssd1306_data([0xf0]*1024)

# There is no way to simply set the pointer, we have to reconfigure the draw area
# There is a four? byte cost to setting the draw area, plus setting it back afterwards
# Go through each byte
#  If there are differences, we have to transmit
#  If there aren't, we *might* transmit

col_start = 0
col_end = 127
page_start = 0
page_end = 7

def setDrawArea(ca, cb, pa):
    global col_start, col_end, page_start, page_end
    if (col_start!=ca or col_end!=cb) and (page_start!=pa):
        ssd1306_cmd([0x21, ca, cb, 0x22, pa, page_end])
        col_start=ca
        col_end=cb
        page_start=pa
    elif col_start!=ca or col_end!=cb:
        ssd1306_cmd([0x21, ca, cb])
        col_start=ca
        col_end=cb
    elif page_start!=pa:
        ssd1306_cmd([0x22, pa, page_end])
        page_start=pa
      

cost = 8

import time


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
            #print(start,end, start%128)
            # at this point, we need to worry about if the transaction crosses a page boundary
            # if start_col != 0 and start_page != end_page, split transaction
            if start%128 != 0 and start//128 !=end//128:
                split_point = ((start//128)+1)*128
                transactions.append((start, split_point-1))
                transactions.append((split_point, end))
                #print("transaction split")
            else:
                transactions.append((start, end))
        else:
            i+=1
    
    # optimise: transactions on adjacent pages with similar start and end col can be combined
    
    for start, end in transactions:
        setDrawArea( start%128, end%128, start//128 )
        ssd1306_data( newbuffer[start:end] )
    #    print(start%128, end%128, start//128 )

    oldbuffer = newbuffer


