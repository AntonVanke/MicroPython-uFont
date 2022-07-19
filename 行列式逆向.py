from machine import Pin, I2C
import ssd1306
import time
import gc

i2c = I2C(scl=Pin(5), sda=Pin(26), freq=100000)
OLED = ssd1306.SSD1306_I2C(128, 64, i2c)

with open("msz.bmf", "rb") as bmf:
    bmf.seek(0, 0)
    version = bmf.read(1)
    bmf.seek(1, 0)
    start = bmf.read(3)
    start = (start[0] << 16) + (start[1] << 8) + start[2]
    bmf.seek(9, 0)
    words = bmf.read(start - 9).decode("utf-8")
    print("已载入字体，BMF 版本号：", version[0])

bmf_file = open("msz.bmf", "rb")


def get_bitmap(word):
    index = words.find(word)
    if index == -1:
        return [0x00, 0x7F, 0x7F, 0x67, 0x6B, 0x75, 0x7A, 0x7D, 0x7D, 0x7A, 0x75, 0x6B, 0x67, 0x7F, 0x7F, 0x00, 0x00,
                0xFE, 0xFE, 0xE6, 0xD6, 0xAE, 0x5E, 0xBE, 0xBE, 0x5E, 0xAE, 0xD6, 0xE6, 0xFE, 0xFE, 0x00]
    bmf_file.seek(start + 32 * index, 0)
    return list(bmf_file.read(32))


def chinese(ch_str, x_axis, y_axis):
    offset_ = 0
    y_axis = y_axis * 8  # 中文高度一行占8个
    x_axis = (x_axis * 16)  # 中文宽度占16个
    for k in ch_str:
        byte_data = get_bitmap(k)
        for y in range(0, 16):
            a_ = bin(byte_data[y]).replace('0b', '')
            while len(a_) < 8:
                a_ = '0' + a_
            b_ = bin(byte_data[y + 16]).replace('0b', '')
            while len(b_) < 8:
                b_ = '0' + b_
            for x in range(0, 8):
                OLED.pixel(x_axis + offset_ + x, y + y_axis, int(a_[x]))
                OLED.pixel(x_axis + offset_ + x + 8, y + y_axis, int(b_[x]))
        offset_ += 16


print(gc.mem_free())
chinese("ABCDEFGH，", 0, 0)
chinese("百年你病独登台。", 0, 2)
chinese("艰难苦恨繁霜鬓，", 0, 4)
chinese("潦倒新停浊酒杯。", 0, 6)
