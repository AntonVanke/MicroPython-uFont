import struct

import numpy as np
from PIL import Image


class Font:
    def __init__(self, display, font_file, reverse=False, dtype="ssd1306"):
        """
        :param display: 显示对象
        :param font_file: bmf 字体文件
        :param reverse: 是否反转颜色
        :param dtype: 显示器类型
        """
        self.display = display
        self.dtype = str(dtype)
        self.reverse = reverse

        with open(font_file, "rb") as self.bmf:
            # 验证格式
            self.bmf.seek(0, 0)
            if self.bmf.read(2).decode() != "BM":
                raise TypeError("不支持的字体文件类型!" + font_file)

            # 读取版本
            self.bmf.seek(2, 0)
            self.version = self.bmf.read(1)

            if str(self.version[0]) != "2":
                raise TypeError("不支持的字体版本: " + font_file + "/v" + str(self.version[0]))

            # 起始位
            self.bmf.seek(4, 0)
            self.start = self.bmf.read(3)
            self.start = (self.start[0] << 16) + (self.start[1] << 8) + self.start[2]

            # 索引
            self.bmf.seek(16, 0)
            self.words = self.bmf.read(self.start - 16).decode("utf-8")

            # 查找缓存
            self.cache = ["", []]
            self.cache_point = 0x00

        # 载入字体文件
        self.bmf_file = open(font_file, "rb")

    def get_bitmap(self, word):
        cindex = self.cache[0].find(word)

        if cindex != -1:
            self.bmf_file.seek(self.start + 32 * self.cache[1][cindex], 0)
            return list(self.bmf_file.read(32))

        index = self.words.find(word)
        if index == -1:
            return [0xff, 0xff, 0xff, 0xff, 0xf8, 0x0f, 0xe7, 0xe7, 0xcf, 0xf3, 0xc7, 0xf3, 0xff, 0xc7, 0xff, 0x1f,
                    0xff, 0x3f, 0xff, 0x7f, 0xff, 0xff, 0xff, 0xff, 0xfe, 0x7f, 0xfc, 0x3f, 0xfe, 0x7f, 0xff, 0xff]
        self.bmf_file.seek(self.start + 32 * index, 0)

        if len(self.cache[0]) <= 100:
            self.cache[0] += word
            self.cache[1].append(index)
        else:
            self.cache[0][self.cache_point] = word
            self.cache[1][self.cache_point] = index
            if self.cache_point < 99:
                self.cache_point += 1
            else:
                self.cache_point = 0

        return list(self.bmf_file.read(32))


font = Font(None, "unifont-14-7000.v2.bmf")


def list_to_bin(arr):
    for _ in range(len(arr)):
        b = []
        for i in range(7, -1, -1):
            b.append(arr[_] >> i & 1)
        arr[_] = b
    return np.asarray(arr).reshape((-1, 16))


def show_bitmap(arr):
    """
    显示点阵字 MONO_HLSB
    :return:
    """
    for row in arr:
        for i in row:
            if i:
                print('*', end=' ')
            else:
                print('.', end=' ')
        print()


print(list_to_bin(font.get_bitmap("我")))
show_bitmap(list_to_bin(font.get_bitmap("我")))
# buf = framebuf.FrameBuffer(
#     [0x00, 0x01, 0x06, 0x1F, 0xE0, 0x02, 0x04, 0x18, 0xF0, 0x10, 0x13, 0x10, 0x10, 0x14, 0x18, 0x00, 0x80, 0x00, 0x00,
#      0xFF, 0x00, 0x08, 0x30, 0xC0, 0x02, 0x01, 0xFE, 0x00, 0x80, 0x60, 0x18, 0x00], 16, 16, framebuf.MONO_HLSB)
# OLED.blit(buf, 0, 0)
# [32, 0, 0, 0, 0, 0, 1, 15, 56, 19, 4, 28, 53, 4, 7, 6, 4, 0, 0, 0, 96, 128, 0, 252, 0, 56, 68, 4, 254, 248, 0, 32]
# [64, 64, 64, 0, 0, 4, 6, 12, 9, 10, 26, 40, 73, 74, 10, 10, 9, 0, 0, 0, 0, 64, 192, 128, 252, 24, 80, 96, 96, 110, 102, 98]

# [0x00,0x01,0x06,0x1F,0xE0,0x02,0x04,0x18,0xF0,0x10,0x13,0x10,0x10,0x14,0x18,0x00, 0x80,0x00,0x00,0xFF,0x00,0x08,0x30,0xC0,0x02,0x01,0xFE,0x00,0x80,0x60,0x18,0x00]
#
# [0x08,0x08,0x08,0x11,0x11,0x32,0x34,0x50,0x91,0x11,0x12,0x12,0x14,0x10,0x10,0x10,0x80,0x80,0x80,0xFE,0x02,0x04,0x20,0x20,0x28,0x24,0x24,0x22,0x22,0x20,0xA0,0x40]
#

# [0,0x1F,0xF8,0x1F,0xF8,0x1F,0xF8,0x1F,0xF8,0x1F,0xF8,0x1F,0x07,0xE0,0x07,0xE0,0x07,0xE0,0x07,0xE0,0xFF,0xFF,0xF8,0x1F,0xF8,0x1F,0xF8,0x1F,0xF8,0x1F,0xF8,0x1F]
# [0x10,0x01,0x10,0x01,0x10,0x01,0x88,0x7F,0x88,0x40,0x4C,0x20,0x2C,0x04,0x0A,0x04,0x89,0x14,0x88,0x24,0x48,0x24,0x48,0x44,0x28,0x44,0x08,0x04,0x08,0x05,0x08,0x02]
