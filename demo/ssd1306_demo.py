"""
SSD1306(OLED 128*64) 屏幕中文测试
Micropython版本: 1.19.1
演示硬件:
    SSD1306(OLED 128*64 IIC)
    合宙ESP32C3(without ch343)
所需文件:
    ufont.py
    unifont-14-12917-16.v3.bmf
    ssd1306.py
链接引脚:
    SCL = 2
    SDA = 3
使用字体: unifont-14-12917-16.v3.bmf
"""
import time

from machine import I2C, Pin

import ufont
import ssd1306


def wait(info, _t=5):
    print(info)
    time.sleep(_t)


# 请修改为对应 FootPrint
i2c = I2C(scl=Pin(2), sda=Pin(3))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

# 载入字体
#   使用字体制作工具：https://github.com/AntonVanke/MicroPython_BitMap_Tools
font = ufont.BMFont("unifont-14-12917-16.v3.bmf")

wait("""
# 最简单的显示 "你好"
#   其中指定 `show=True` 使得屏幕及时更新
""", 6)
font.text(display, "你好", 0, 0, show=True)

wait("""
# 如果想让文字显示在屏幕正中间，可以通过指定文本左上角位置来修改显示位置
""", 5)
font.text(display, "你好", 48, 16, show=True)

wait("""
# 此时你会发现：上一次显示显示的文字不会消失。因为你没有指定清屏参数：`clear=True`;让我们再试一次
#   注意，请使用修改后的 `ssd1306.py` 驱动，否则请自行调用`display.fill(0)`
""", 10)
font.text(display, "你好", 48, 16, show=True, clear=True)

wait("""
# 显示英文呢？
""", 3)
font.text(display, "He110", 48, 8, show=True, clear=True)
font.text(display, "你好", 48, 24, show=True)

wait("""
# 会发现一个汉字的宽度大概是字母的两倍，如果你需要等宽，可以指定参数 `half_char=False`
""", 6)
font.text(display, "HELLO", 32, 16, show=True, clear=True, half_char=False)

wait("""
# 显示的文字如果很长，会超出屏幕边界，例如：
""", 3)
poem = "他日若遂凌云志，敢笑黄巢不丈夫!"
font.text(display, poem, 0, 8, show=True, clear=True)

wait("""
# 此时，需要指定参数 `auto_wrap=True` 来自动换行
""", 5)
font.text(display, poem, 0, 8, show=True, clear=True, auto_wrap=True)

wait("""
# 自动换行的行间距太小了？
#   添加 `line_spacing: int` 参数来调整行间距, 此处指定 8 个像素
""", 8)
font.text(display, poem, 0, 8, show=True, clear=True, auto_wrap=True, line_spacing=8)

wait("""
# 调整字体大小，可以指定 `font_size: int` 参数
#   注意：这会严重增加运行时间
""", 8)
font.text(display, "T:15℃", 24, 8, font_size=32, show=True, clear=True)

wait("""
# 当你使用墨水屏时，颜色可能会出现反转。或者你主动想要颜色反转
#   可以指定参数 `reverse=Ture`
""", 8)
font.text(display, "T:15℃", 24, 8, font_size=32, show=True, clear=True, reverse=True)
