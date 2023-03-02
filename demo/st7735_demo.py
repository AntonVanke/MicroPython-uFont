"""
ST7735(LCD 160*80) 屏幕中文测试
Micropython版本: 1.19.1
演示硬件:
    合宙 Air10x 系列屏幕扩展板
    合宙ESP32C3(without ch343)
所需文件:
    ufont.py
    unifont-14-12917-16.v3.bmf
    st7735.py
链接引脚:
    SCL = 2
    SDA = 3
    RST = 10
    DC  = 6
    CS  = 7
    BL  = 11
使用字体: unifont-14-12917-16.v3.bmf
"""
import random
import time

from machine import SPI, Pin

import ufont
from st7735 import ST7735

# 请修改为对应 FootPrint
spi = SPI(1, 30000000, sck=Pin(2), mosi=Pin(3))
display = ST7735(spi=spi, cs=7, dc=6, rst=10, bl=11, width=160, height=80, rotate=1)


def wait(info, _t=5):
    print(info)
    time.sleep(_t)


# 载入字体
#   使用字体制作工具：https://github.com/AntonVanke/MicroPython-ufont-Tools
font = ufont.BMFont("unifont-14-12917-16.v3.bmf")

wait("""
# 最简单的显示 "你好"
#   其中指定 `show=True` 使得屏幕及时更新
""", 6)
font.text(display, "你好", 0, 0, show=True)

wait("""
# 如果想让文字显示在屏幕正中间，可以通过指定文本左上角位置来修改显示位置
""", 5)
font.text(display, "你好", 64, 32, show=True)

wait("""
# 此时你会发现：上一次显示显示的文字不会消失。因为你没有指定清屏参数：`clear=True`;让我们再试一次
""", 6)
font.text(display, "你好", 64, 32, show=True, clear=True)

wait("""
# 显示英文呢？
""", 3)
font.text(display, "He110", 64, 26, show=True, clear=True)
font.text(display, "你好", 64, 42, show=True)

wait("""
# 会发现一个汉字的宽度大概是字母的两倍，如果你需要等宽，可以指定参数 `half_char=False`
""", 6)
font.text(display, "HELLO", 48, 24, show=True, clear=True, half_char=False)

wait("""
# 可以通过指定参数 `color` 来指定字体颜色，其中 color 是 RGB565 格式
""", 6)
font.text(display, "hello", 48, 32, color=0xff00, show=True)

wait("""
# 同样，我们可以通过指定 `bg_color` 参数调整背景颜色
""")
font.text(display, "你好", 56, 28, color=0xff00, bg_color=0x00ff, show=True)

wait("""
# 大一点？可以使用 `font_size` 指定字号大小
#   注意：放大彩色字体对内存的要求十分巨大
""")
font.text(display, "Temp: 15℃", 0, 26, font_size=32, color=0xff00, bg_color=0x00ff, show=True, clear=True)
