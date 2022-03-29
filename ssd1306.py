import io, fcntl

dev = "/dev/i2c-4"
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

while True:
    raw = root.get_image(x,y,w,h, X.ZPixmap, 0xffffffff)
    simg = Image.frombytes("RGB", (w, h), raw.data, "raw", "BGRX")

    pointer = root.query_pointer()
    px, py = pointer.root_x, pointer.root_y
    if px > x and py < h:
        iarray, xhot, yhot = cursor.getCursorImageArrayFast()
        cimg = Image.fromarray(iarray)
        simg.paste(cimg, (px-x-xhot,py-y-yhot), cimg) 
    
    b = simg.convert("1").rotate(-90,expand=True).tobytes()
    r = np.frombuffer(b, np.uint8).reshape(w,h//8)
    r = np.transpose(r)
    r = np.flip(r, 0)
    
    ssd1306_data(list(r.tobytes()))

