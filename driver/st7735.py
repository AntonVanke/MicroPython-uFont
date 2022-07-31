# https://github.com/enesbcs/mpyeasy-async/blob/b21a330a467030896ee939113d52be47692f5d33/src/inc/st7735.py
import framebuf
import time
from machine import Pin

TFTBGR = 0x08  # When set color is bgr else rgb.
TFTRGB = 0x00
# TFTRotations = [0x08, 0x68, 0xC8, 0xA8]
TFTRotations = [0x00, 0x60, 0xC0, 0xA0]


class ST7735(framebuf.FrameBuffer):
    def __init__(self, spi, cs, dc, rst=None, width=80, height=160, disptype='r', xoffset=0, yoffset=0, rotate=0,
                 rgb=True):
        self.cs = Pin(cs, Pin.OUT, value=1)
        self.dc = Pin(dc, Pin.OUT, value=1)
        if rst is not None:
            self.rst = Pin(rst, Pin.OUT, value=1)
            self.rst.on()
            time.sleep_ms(5)
            self.rst.off()
            time.sleep_ms(20)
            self.rst.on()
            time.sleep_ms(150)
        else:
            self.rst = None
        self.spi = spi
        if rotate == 90:
            self.rotate = 1
        elif rotate == 180:
            self.rotate = 2
        elif rotate == 270:
            self.rotate = 3
        else:
            self.rotate = 0
        self.disptype = disptype
        self.width = width
        self.height = height
        self.xoffset = xoffset
        self.yoffset = yoffset
        self._rgb = rgb
        self.initialized = False
        try:
            self.buffer = bytearray(self.width * self.height * 2)
        except:
            return
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        try:
            self.init_display()
            self.initialized = True
        except:
            pass

    def init_display(self):  # red tab  / m5stickc
        if self.disptype == 'r':
            self.init_display_r()
        elif self.disptype == 'b':
            self.init_display_b()
        elif self.disptype == 'b2':
            self.init_display_b2()
        elif self.disptype == 'g':
            self.init_display_g()
        self.clear()

    def init_display_r(self):  # red tab  / m5stickc
        cols = bytearray(4)
        rows = bytearray(4)
        cols[1] = self.xoffset
        rows[1] = self.yoffset
        cols[3] = self.width - 1 + self.xoffset
        rows[3] = self.height - 1 + self.yoffset
        for cmd, data, delay in [
            (0x01, None, 150),  # SWRESET
            (0x11, None, 500),  # SLPOUT
            (0xb1, b'\x01\x2c\x2d', None),  # FRMCTR1
            (0xb2, b'\x01\x2c\x2d', None),  # FRMCTR2
            (0xb3, b'\x01\x2c\x2d\x01\x2c\x2d', None),  # FRMCTR3
            (0xb4, b'\x07', None),  # INVCTR
            (0xc0, b'\xa2\x02\x84', None),  # PWCTR1
            (0xc1, b'\xc5', None),  # PWCTR2
            (0xc2, b'\x0a\x00', None),  # PWCTR3
            (0xc3, b'\x8a\x2a', None),  # PWCTR4
            (0xc4, b'\x8a\xee', None),  # PWCTR5
            (0xc5, b'\x0e', None),  # VMCTR1
            (0x20, None, None),  # INVOFF
            (0x36, b'\xc8', None),  # MADCTL
            (0x3a, b'\x05', None),  # COLMOD
            (0x2a, cols, None),  # Column address set.
            (0x2b, rows, None),  # Row address set.
            (0x21, None, None),  # INVON
            (0xe0, b'\x02\x1c\x07\x12\x37\x32\x29\x2d\x29\x25\x2b\x39\x00\x01\x03\x10', None),  # GMCTRP1
            (0xe1, b'\x03\x1d\x07\x06\x2e\x2c\x29\x2d\x2e\x2e\x37\x3f\x00\x00\x02\x10', None),  # GMCTRN1
            (0x13, None, 10),  # NORON
            (0x29, None, 100),  # DISPON
            (0x36, b'\xcc', 10),  # MADCTL
        ]:
            self.write_cmd(cmd)
            if data:
                self.write_data(data)
            if delay:
                time.sleep_ms(delay)

    def init_display_b(self):  # blue tab
        cols = bytearray(4)
        rows = bytearray(4)
        self.xoffset = 2
        self.yoffset = 1
        cols[1] = self.xoffset
        rows[1] = self.yoffset
        cols[3] = self.width - 1 + self.xoffset
        rows[3] = self.height - 1 + self.yoffset
        for cmd, data, delay in [
            (0x01, None, 50),  # SWRESET
            (0x11, None, 500),  # SLPOUT
            (0x3a, b'\x05', 10),  # COLMOD
            (0xb1, b'\x00\x06\x03', 10),  # FRMCTR1
            (0x36, b'\x08', None),  # MADCTL
            (0xb6, b'\x15\x02', None),  # DISSET5
            (0xb4, b'\x00', None),  # INVCTR
            (0xc0, b'\x02\x70', 10),  # PWCTR1
            (0xc1, b'\x05', None),  # PWCTR2
            (0xc2, b'\x01\x02', None),  # PWCTR3
            (0xc5, b'\x3c\x38', 10),  # VMCTR1
            (0xfc, b'\x11\x15', None),  # PWCTR6
            (0xe0, b'\x02\x1c\x07\x12\x37\x32\x29\x2d\x29\x25\x2b\x39\x00\x01\x03\x10', None),  # GMCTRP1
            (0xe1, b'\x03\x1d\x07\x06\x2e\x2c\x29\x2d\x2e\x2e\x37\x3f\x00\x00\x02\x10', 10),  # GMCTRN1
            (0x2a, cols, None),  # Column address set.
            (0x2b, rows, None),  # Row address set.
            (0x13, None, 10),  # NORON
            (0x2c, None, 500),  # RAMWR
            (0x29, None, 500),  # DISPON
        ]:
            self.write_cmd(cmd)
            if data:
                self.write_data(data)
            if delay:
                time.sleep_ms(delay)

    def init_display_b2(self):  # blue tab2
        cols = bytearray(4)
        rows = bytearray(4)
        self.xoffset = 2
        self.yoffset = 1
        cols[1] = self.xoffset
        rows[1] = self.yoffset
        cols[3] = self.width - 1 + self.xoffset
        rows[3] = self.height - 1 + self.yoffset
        for cmd, data, delay in [
            (0x01, None, 50),  # SWRESET
            (0x11, None, 500),  # SLPOUT
            (0xb1, b'\x01\x2c\x2d', 10),  # FRMCTR1
            (0xb2, b'\x01\x2c\x2d', 10),  # FRMCTR2
            (0xb3, b'\x01\x2c\x2d', 10),  # FRMCTR3
            (0xb4, b'\x07', None),  # INVCTR
            (0xc0, b'\xa2\x02\x84', 10),  # PWCTR1
            (0xc1, b'\xc5', None),  # PWCTR2
            (0xc2, b'\x0a\x00', None),  # PWCTR3
            (0xc3, b'\x8a\x2a', None),  # PWCTR4
            (0xc4, b'\x8a\xee', None),  # PWCTR5
            (0xc5, b'\x0e', None),  # VMCTR1
            (0x36, b'\xc8', None),  # MADCTL
            (0xe0, b'\x02\x1c\x07\x12\x37\x32\x29\x2d\x29\x25\x2b\x39\x00\x01\x03\x10', None),  # GMCTRP1
            (0xe1, b'\x03\x1d\x07\x06\x2e\x2c\x29\x2d\x2e\x2e\x37\x3f\x00\x00\x02\x10', 10),  # GMCTRN1
            (0x2a, cols, None),  # Column address set.
            (0x2b, rows, None),  # Row address set.
            (0x3a, b'\x05', 10),  # COLMOD
            (0x13, None, 10),  # NORON
            (0x2c, None, 500),  # RAMWR
            (0x29, None, 500),  # DISPON
        ]:
            self.write_cmd(cmd)
            if data:
                self.write_data(data)
            if delay:
                time.sleep_ms(delay)

    def init_display_g(self):  # green tab
        cols = bytearray(4)
        rows = bytearray(4)
        cols[1] = self.xoffset
        rows[1] = self.yoffset
        cols[3] = self.width - 1 + self.xoffset
        rows[3] = self.height - 1 + self.yoffset
        rgb = TFTRGB if self._rgb else TFTBGR
        maddata = bytearray([TFTRotations[self.rotate] | rgb])
        for cmd, data, delay in [
            (0x01, None, 150),  # SWRESET
            (0x11, None, 255),  # SLPOUT
            (0xb1, b'\x01\x2c\x2d', None),  # FRMCTR1
            (0xb2, b'\x01\x2c\x2d', None),  # FRMCTR2
            (0xb3, b'\x01\x2c\x2d\x01\x2c\x2d', 10),  # FRMCTR3
            (0xb4, b'\x07', None),  # INVCTR
            (0xc0, b'\xa2\x02\x84', None),  # PWCTR1
            (0xc1, b'\xc5', None),  # PWCTR2
            (0xc2, b'\x0a\x00', None),  # PWCTR3
            (0xc3, b'\x8a\x2a', None),  # PWCTR4
            (0xc4, b'\x8a\xee', None),  # PWCTR5
            (0xc5, b'\x0e', None),  # VMCTR1
            (0x20, None, None),  # INVOFF
            (0x36, maddata, None),  # MADCTL
            (0x3a, b'\x05', None),  # COLMOD
            (0x2a, cols, None),  # Column address set.
            (0x2b, rows, None),  # Row address set.
            (0x21, None, None),  # INVON
            (0xe0, b'\x02\x1c\x07\x12\x37\x32\x29\x2d\x29\x25\x2b\x39\x00\x01\x03\x10', None),  # GMCTRP1
            (0xe1, b'\x03\x1d\x07\x06\x2e\x2c\x29\x2d\x2e\x2e\x37\x3f\x00\x00\x02\x10', None),  # GMCTRN1
            (0x13, None, 10),  # NORON
            (0x29, None, 100),  # DISPON
        ]:
            self.write_cmd(cmd)
            if data:
                self.write_data(data)
            if delay:
                time.sleep_ms(delay)

    def rgb(self, aTF=True):
        '''True = rgb else bgr'''
        self._rgb = aTF
        self._setMADCTL()

    def rotation(self, aRot):
        '''0 - 3. Starts vertical with top toward pins and rotates 90 deg
           clockwise each step.'''
        if (0 <= aRot < 4):
            rotchange = self.rotate ^ aRot
            self.rotate = aRot
            # If switching from vertical to horizontal swap x,y
            # (indicated by bit 0 changing).
            if (rotchange & 1):
                i = self.width
                self.width = self.height
                self.height = i
                i = self.xoffset
                self.xoffset = self.yoffset
                self.yoffset = i
            self._setMADCTL()

    def _setMADCTL(self):
        self.write_cmd(0x36)
        rgb = TFTRGB if self._rgb else TFTBGR
        self.write_data(bytearray([TFTRotations[self.rotate] | rgb]))

    def clear(self):
        self.fill(0)
        self.show()

    def show(self):
        cols = bytearray(4)
        rows = bytearray(4)
        cols[1] += self.xoffset
        cols[3] = self.width - 1 + self.xoffset
        rows[1] += self.yoffset
        rows[3] = self.height - 1 + self.yoffset
        self.write_cmd(0x2a)
        self.write_data(cols)
        self.write_cmd(0x2b)
        self.write_data(rows)
        self.write_cmd(0x2c)
        self.write_data(self.buffer)

    def write_cmd(self, cmd):
        self.dc.off()
        self.cs.off()
        self.spi.write(bytes([cmd]))
        self.cs.on()

    def write_data(self, buf):
        self.dc.on()
        self.cs.off()
        self.spi.write(buf)
        self.cs.on()
