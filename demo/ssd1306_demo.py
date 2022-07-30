"""
SSD1306(OLED 128*64) 屏幕中文测试
I2C 引脚:
    SCL = 2
    SDA = 3
使用字体: unifont-14-12888-16.v3.bmf
"""
import time
import random

from machine import Pin, I2C

import ssd1306
import ufont

i2c = I2C(scl=Pin(2), sda=Pin(3))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
poem_info = "\t登高\n唐·杜甫"
poem = "风急天高猿啸哀渚清沙白鸟飞回无边落木萧萧下不尽长江滚滚来万里悲秋常作客百年多病独登台艰难苦恨繁霜鬓潦倒新停浊酒杯"
f = ufont.BMFont("unifont-14-12888-16.v3.bmf")


def test1():
    print("测试1")
    f.text(display=display, string=poem_info, x=32, y=10, font_size=16, clear=True, show=True)
    for _ in range(0, len(poem), 7):
        time.sleep(0.5)
        f.text(display=display, string=poem[_: _ + 7], x=8, y=24, font_size=16, clear=True, show=True)


def test2():
    print("测试3")
    f.text(display=display, string="测试Test", x=0, y=0, font_size=16, show=True, clear=True)
    f.text(display=display, string="测试Test", x=0, y=16, font_size=20, show=True)
    f.text(display=display, string="测试Test", x=0, y=34, font_size=32, show=True)
    f.text(display=display, string="OK", x=40, y=8, font_size=48, show=True)


f.text(display=display, string="SSD1306\n(OLED 128*64)\n屏幕中文测试\n使用字体:unifont", x=0, y=0, font_size=16, show=True,
       clear=True)
time.sleep(5)
test1()
time.sleep(1)
test2()
