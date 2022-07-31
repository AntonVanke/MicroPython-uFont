from machine import SPI, Pin
from e1in54 import EPD
import time
import ufont

spi = SPI(1, 30000000, sck=Pin(2), mosi=Pin(3))
display = EPD(spi, cs=18, dc=12, rst=1, busy=19)
poem_info = "\t登高\n唐·杜甫"
poem = "风急天高猿啸哀渚清沙白鸟飞回无边落木萧萧下不尽长江滚滚来万里悲秋常作客百年多病独登台艰难苦恨繁霜鬓潦倒新停浊酒杯"
f = ufont.BMFont("unifont-14-12888-16.v3.bmf")


def test1():
    display.fill(1)
    display.set_refresh(True)
    f.text(display, poem_info, 40, 50, font_size=32, reverse=True, clear=True, show=True)
    display.set_refresh(False)
    f.clear(display, 1)
    for _ in range(0, len(poem), 7):
        time.sleep(0.8)
        f.text(display=display, string=poem[_: _ + 7], x=2, y=(_ // 7) * 25, font_size=25, clear=False, show=True,
               reverse=True)
    display.set_refresh(True)


def test2():
    f.text(display=display, string="测试Test", x=0, y=0, font_size=16, show=True, clear=True, reverse=True)
    f.text(display=display, string="测试Test", x=0, y=16, font_size=24, show=True)
    f.text(display=display, string="测试Test", x=0, y=40, font_size=32, show=True, reverse=True)
    display.set_refresh(False)
    f.text(display=display, string="测试Test", x=0, y=72, font_size=40, show=True, reverse=False)
    f.text(display=display, string="测试Test", x=0, y=112, font_size=48, show=True, reverse=True)
    f.text(display=display, string="ePaperTest", x=0, y=160, font_size=40, show=True, reverse=False)
    f.text(display=display, string="O\nK", x=152, y=0, font_size=48, show=True)
    display.set_refresh(True)


test1()
test2()
