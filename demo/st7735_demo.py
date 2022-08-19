from machine import SPI, Pin
import time
import random

import ufont
from st7735 import ST7735, color

poem_info = "\t登高\n唐·杜甫"
poem = "风急天高猿啸哀渚清沙白鸟飞回无边落木萧萧下不尽长江滚滚来万里悲秋常作客百年多病独登台艰难苦恨繁霜鬓潦倒新停浊酒杯"

spi = SPI(1, 30000000, sck=Pin(2), mosi=Pin(3))
display = ST7735(spi=spi, cs=18, dc=12, rst=1, bl=19, width=80, height=160, rotate=0)
f = ufont.BMFont("unifont-14-12888-16.v3.bmf")


def test1():
    f.text(display=display, string=poem_info,
           color=color(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)), x=32, y=64,
           font_size=16, clear=True, show=True)
    for _ in range(0, len(poem), 7):
        time.sleep(0.8)
        f.text(display=display, string=poem[_: _ + 7], x=8, y=70,
               color=color(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)),
               font_size=16, clear=True, show=True)


def test2():
    f.text(display=display, string="测试Test", x=0, y=0,
           color=color(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)), font_size=16,
           show=True, clear=True)
    f.text(display=display, string="测试Test", x=0, y=16,
           color=color(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)), font_size=22,
           show=True)
    f.text(display=display, string="测试Test", x=0, y=34,
           color=color(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)), font_size=32,
           show=True)
    f.text(display=display, string="OK", x=80, y=-10,
           color=color(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)), font_size=48,
           show=True)


f.text(display=display, string="ST7735\n(TFT 128*160)\n屏幕中文测试\n使用字体:unifont", color=color(255, 255, 255), x=0, y=40,
       font_size=16, show=True,
       clear=True)
time.sleep(5)
test1()
time.sleep(1)
test2()
