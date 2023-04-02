__version__ = "2.0.1"
"""
ST77XX 通用驱动 v2.0.1
支持 ST7789 和 ST7735 的驱动，采用 FrameBuffer(RGB565) 缓冲整个屏幕数据，内存较小勿用

内存计算方式:
    width * height * 2(Byte)

使用方法(以 [合宙ESP32C3] + [合宙 Air10x 系列屏幕扩展板] 直插为例):
    from machine import SPI, Pin
    from st77xx import ST77XX

    spi = SPI(1, 30000000, sck=Pin(2), mosi=Pin(3), polarity=1)
    ST7735(spi, rst=10, dc=6, cs=7, bl=11, width=160, height=80, rotate=1)  # 直插横屏显示
    ST7735(spi, rst=10, dc=6, cs=7, bl=11, width=160, height=80, rotate=0)  # 直插竖屏显示

偏移问题:
    默认提供了三种屏幕的偏移数据(160*80, 160*128, 240*240)，偏移不正确或者没有预设，请自行指定偏移，例如:
        ST7789(spi, rst=6, dc=5, bl=4, width=240, height=135, rotate=0, offset=(0, 0, 240, 135))

颜色问题:
    不同厂商生产的屏幕可能会有颜色错误，可以更改 `rgb` 和 `inverse` 参数来校准颜色，例如:
        d = ST7789(spi, rst=6, dc=5, bl=4, width=240, height=135, rotate=0, rgb=True, inverse=True)
        d = ST7789(spi, rst=6, dc=5, bl=4, width=240, height=135, rotate=0, rgb=True, inverse=False)
        ......

无法显示问题:
    查看并尝试更改 SPI的 polarity/firstbit/phase 参数，参考文档：
        https://docs.micropython.org/en/latest/library/machine.SPI.html#machine.SoftSPI
        
ST7735S文档: https://www.waveshare.net/w/upload/e/e2/ST7735S_V1.1_20111121.pdf
ST7789文档: https://www.waveshare.com/w/upload/a/ae/ST7789_Datasheet.pdf

FrameBuf 文档: https://docs.micropython.org/en/latest/library/framebuf.html
字库文档: https://github.com/AntonVanke/MicroPython-uFont
字体生成工具：https://github.com/AntonVanke/MicroPython-uFont-Tools
自用 Micropython 驱动库：https://github.com/AntonVanke/MicroPython-Drivers
"""
import gc
import time
import math

import machine
import framebuf
from micropython import const

SWRESET = const(0x01)
SLPOUT = const(0x11)
NORON = const(0x13)

INVOFF = const(0x20)
DISPON = const(0x29)
CASET = const(0x2A)
RASET = const(0x2B)
RAMWR = const(0x2C)

MADCTL = const(0x36)
COLMOD = const(0x3A)

FRMCTR1 = const(0xB1)
FRMCTR2 = const(0xB2)
FRMCTR3 = const(0xB3)

INVCTR = const(0xB4)

PWCTR1 = const(0xC0)
PWCTR2 = const(0xC1)
PWCTR3 = const(0xC2)
PWCTR4 = const(0xC3)
PWCTR5 = const(0xC4)
VMCTR1 = const(0xC5)

GMCTRP1 = const(0xE0)
GMCTRN1 = const(0xE1)

# 旋转方向
ROTATIONS = [0x00, 0x60, 0xC0, 0xA0]

# 预设偏移
TYPE_A_OFFSET = [(24, 0, 103, 160), (0, 24, 160, 104), (24, 0, 103, 160), (0, 24, 160, 104)]  # 80x160
TYPE_B_OFFSET = [(0, 0, 128, 160), (0, 0, 160, 128), (0, 0, 128, 160), (0, 0, 160, 128)]  # 128x160
TYPE_C_OFFSET = [(0, 0, 239, 240), (0, 0, 240, 240), (80, 0, 320, 240), (0, 80, 240, 320)]  # 240x240


def color(r, g, b):
    i = (((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)).to_bytes(2, "little")
    return (i[0] << 8) + i[1]


RED = color(255, 0, 0)
GREEN = color(0, 255, 0)
BLUE = color(0, 0, 255)
WHITE = color(255, 255, 255)
BLACK = color(0, 0, 0)


class ST77XX(framebuf.FrameBuffer):
    def __init__(self, spi, rst, dc, cs=None, bl=None, width=80, height=160, offset=(0, 0, 0, 0), rotate=1,
                 rgb=True, inverse=False, **kwargs):
        """
        :param spi:
        :param rst:
        :param dc:
        :param cs: 使能
        :param bl: 背光
        :param width: 宽度
        :param height: 高度
        :param offset: 偏移
        :param rotate: 旋转
        :param rgb: RGB 色彩模式
        """
        # 根据方向自动设置偏移
        self.rotate = rotate
        self.offset = offset
        self.inverse = inverse
        self.rgb = rgb
        self.width = width
        self.height = height

        self.spi = spi
        self.rst = machine.Pin(rst, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.dc = machine.Pin(dc, machine.Pin.OUT, machine.Pin.PULL_DOWN)

        # 有的没有cs引脚
        if cs is not None:
            self.cs = machine.Pin(cs, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        else:
            self.cs = int
        if bl is not None:
            self.bl = machine.PWM(machine.Pin(bl), duty=1023)
        self.auto_offset() if self.offset == (0, 0, 0, 0) else 0

        gc.collect()
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init()
        self.set_windows()
        self.clear()

    def auto_offset(self, _rotate: int = None):
        _rotate = self.rotate if _rotate is None else None
        if self.width in [80, 160] and self.height in [80, 160]:
            self.offset = TYPE_A_OFFSET[_rotate]
        elif self.width in [128, 160] and self.height in [128, 160]:
            self.offset = TYPE_B_OFFSET[_rotate]
        elif self.width == 240 and self.height == 240:
            self.offset = TYPE_C_OFFSET[_rotate]
        else:
            self.offset = (0, 0, self.width if _rotate % 2 and self.width > self.height else self.height,
                           self.height if _rotate % 2 and self.width > self.height else self.width)

    def set_windows(self, x_start=None, y_start=None, x_end=None, y_end=None):
        """
        设置窗口
        :return:
        """
        x_start = x_start if x_start else self.offset[0]
        y_start = y_start if y_start else self.offset[1]
        x_end = x_end if x_end else self.offset[2]
        y_end = y_end if y_end else self.offset[3]

        self.write_cmd(CASET)
        self.write_data(bytearray([x_start >> 8, x_start & 0xff, x_end >> 8, x_end & 0xff]))

        self.write_cmd(RASET)
        self.write_data(bytearray([y_start >> 8, y_start & 0xff, y_end >> 8, y_end & 0xff]))

        self.write_cmd(RAMWR)

    def init(self):
        self.reset()

        self.write_cmd(SWRESET)
        time.sleep_us(150)
        self.write_cmd(SLPOUT)
        time.sleep_us(300)

        self.write_cmd(FRMCTR1)
        self.write_data(bytearray([0x01, 0x2C, 0x2D]))
        self.write_cmd(FRMCTR2)
        self.write_data(bytearray([0x01, 0x2C, 0x2D]))
        self.write_cmd(FRMCTR3)
        self.write_data(bytearray([0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D]))
        time.sleep_us(10)

        self.write_cmd(INVCTR)
        self.write_data(bytearray([0x07]))

        self.write_cmd(PWCTR1)
        self.write_data(bytearray([0xA2, 0x02, 0x84]))
        self.write_cmd(PWCTR2)
        self.write_data(bytearray([0xC5]))
        self.write_cmd(PWCTR3)
        self.write_data(bytearray([0x0A, 0x00]))
        self.write_cmd(PWCTR4)
        self.write_data(bytearray([0x8A, 0x2A]))
        self.write_cmd(PWCTR5)
        self.write_data(bytearray([0x8A, 0xEE]))
        self.write_cmd(VMCTR1)
        self.write_data(bytearray([0x0E]))

        self.write_cmd(INVOFF + int(self.inverse))

        self.write_cmd(MADCTL)
        self.write_data(bytearray([ROTATIONS[self.rotate] | 0x00 if self.rgb else 0x08]))

        self.write_cmd(COLMOD)
        self.write_data(bytearray([0x05]))

        self.write_cmd(GMCTRP1)
        self.write_data(
            bytearray([0x02, 0x1c, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2d, 0x29, 0x25, 0x2b, 0x39, 0x00, 0x01, 0x03, 0x10]))

        self.write_cmd(GMCTRN1)
        self.write_data(
            bytearray([0x03, 0x1d, 0x07, 0x06, 0x2e, 0x2c, 0x29, 0x2d, 0x2e, 0x2e, 0x37, 0x3f, 0x00, 0x00, 0x02, 0x10]))

        self.write_cmd(NORON)
        time.sleep_us(10)

        self.write_cmd(DISPON)
        time.sleep_us(100)

        self.cs(1)

    def reset(self):
        """
        设备重置
        :return:
        """
        self.rst(1)
        time.sleep(0.2)
        self.rst(0)
        time.sleep(0.2)
        self.rst(1)
        time.sleep(0.2)

    def write_cmd(self, cmd):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)

    def back_light(self, value):
        """
        背光调节
        :param value: 背光等级 0 ~ 255
        :return:
        """
        self.bl.freq(1000)
        if value >= 0xff:
            value = 0xff
        data = value * 0xffff >> 8
        self.bl.duty_u16(data)

    def clear(self):
        """
        清屏
        :return:
        """
        self.fill(0)
        self.show()

    def show(self):
        """
        显示
        :return:
        """
        self.set_windows()  # 如果没有这行就会偏移
        self.write_data(self.buffer)

    def circle(self, center, radius, c=color(255, 255, 255), section=100):
        """
        画圆
        :param c: 颜色
        :param center: 中心(x, y)
        :param radius: 半径
        :param section: 分段
        :return:
        """
        arr = []
        for m in range(section + 1):
            x = round(radius * math.cos((2 * math.pi / section) * m - math.pi) + center[0])
            y = round(radius * math.sin((2 * math.pi / section) * m - math.pi) + center[1])
            arr.append([x, y])
        for i in range(len(arr) - 1):
            self.line(*arr[i], *arr[i + 1], c)


class ST7789(ST77XX):
    pass


class ST7735(ST77XX):
    pass
