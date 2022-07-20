from machine import Pin, I2C
import ssd1306
import time

i2c = I2C(sda=Pin(4), scl=Pin(5))
OLED = ssd1306.SSD1306_I2C(128, 64, i2c)
OLED.font("SourceHanSansSC-Light.bmf")

poem = "风急天高猿啸哀，渚清沙白鸟飞回。无边落木萧萧下，不尽长江滚滚来。万里悲秋常作客，百年多病独登台。艰难苦恨繁霜鬓，潦倒新停浊酒杯。"
for p in range(12):
    for i in range(0, len(poem), 8):
        OLED.chinese(poem[i:i + 8], 0, 0 + i * 2 - 16 * p)
    for o in range(16, 65, 16):
        OLED.chinese("                ", 0, o + i * 2 - 16 * p)
    OLED.show()

for t in range(10):
    start = time.ticks_ms()
    for _ in "万里悲秋常作客百年多":
        OLED.chinese(_, 0, 0)
        OLED.show()
    end = time.ticks_ms()
    OLED.chinese("帧数：" + str(10000 / (end - start))[0:5] + "Fps", 0, 16)
OLED.show()