"""
合宙 Air10x 系列屏幕扩展板驱动
160(H)RGB x 80(V)

使用方法(以合宙ESP32C3为例):
    from machine import SPI, Pin
    from st7735 import ST7735

    spi = SPI(1, 30000000, sck=Pin(2), mosi=Pin(3))
    ST7735(spi, rst=10, dc=6, cs=7, bl=11, width=160, height=80, rotate=1)  # 直插横屏显示
    ST7735(spi, rst=10, dc=6, cs=7, bl=11, width=160, height=80, rotate=0)  # 直插竖屏显示

本款LCD使用的内置控制器为ST7735S，是一款162 x RGB x 132像素的LCD控制器,而本LCD本身的像素为160(H)RGB x 80(V)。由于LCD的显示
起始位置与控制器的原点不一致，因此在使用控制器初始化显示全屏显示区域时需要对做偏移处理：水平方向从第二个像素点开始显示，垂直方向从第27个像素点
开始。这样就可以保证显示的LCD中RAM对应的位置与实际一致。(https://www.waveshare.net/wiki/Pico-LCD-0.96)

屏幕详细信息: https://wiki.luatos.com/peripherals/lcd_air10x/index.html
ST7735S文档: https://www.waveshare.net/w/upload/e/e2/ST7735S_V1.1_20111121.pdf
FrameBuf文档: https://docs.micropython.org/en/latest/library/framebuf.html
字体文档: https://github.com/AntonVanke/MicroPython-Chinese-Font
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

ROTATIONS = [0x00, 0x60, 0xC0, 0xA0]  # 旋转方向


def color(r, g, b):
    i = (((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)).to_bytes(2, "little")
    return (i[0] << 8) + i[1]


RED = color(255, 0, 0)
GREEN = color(0, 255, 0)
BLUE = color(0, 0, 255)
WHITE = color(255, 255, 255)
BLACK = color(0, 0, 0)


class ST7735(framebuf.FrameBuffer):
    def __init__(self, spi, rst, dc, cs, bl=None, width=80, height=160, offset=None, rotate=1, rgb=True):
        """
        :param spi:
        :param rst:
        :param dc:
        :param cs: 使能
        :param bl: 背光
        :param width: 宽度
        :param height: 高度
        :param offset: 偏移 (x, y): (23, -1)|(-1, 23)
        :param rotate: 旋转 0 横屏 1 竖屏
        :param rgb: RGB 色彩模式
        """
        # 根据方向自动设置偏移
        self.rotate = rotate
        self.offset = offset
        self.rgb = rgb
        if offset is None and rotate == 1:
            self.offset = (-1, 23)
        elif offset is None and rotate == 0:
            self.offset = (23, -1)
        self.width = width
        self.height = height

        self.spi = spi
        self.rst = machine.Pin(rst, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.dc = machine.Pin(dc, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self.cs = machine.Pin(cs, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        if bl is not None:
            self.bl = machine.PWM(machine.Pin(bl))

        gc.collect()
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init()
        self.set_windows()
        self.clear()

    def set_windows(self, x_start=None, y_start=None, x_end=None, y_end=None):
        """
        设置窗口
        :return:
        """
        x_start = (x_start + self.offset[0] + 1) if x_start is not None else (self.offset[0] + 1)
        x_end = x_end + self.rotate + self.offset[0] if x_end is not None else self.width + self.rotate + \
                                                                               self.offset[0]
        y_start = y_start + self.offset[1] + 1 if y_start is not None else self.offset[1] + 1
        y_end = y_end + self.rotate + self.offset[1] if y_end is not None else self.height + self.rotate + \
                                                                               self.offset[1]

        self.write_cmd(CASET)
        self.write_data(bytearray([0x00, x_start, 0x00, x_end]))

        self.write_cmd(RASET)
        self.write_data(bytearray([0x00, y_start, 0x00, y_end]))

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

        self.write_cmd(INVOFF)

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

    def image(self, file_name):
        with open(file_name, "rb") as bmp:
            for b in range(0, 80 * 160 * 2, 1024):
                self.buffer[b:b + 1024] = bmp.read(1024)
            self.show()
