__version__ = 2

import framebuf


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

    def _get_bitmap(self, word):
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

    def text(self, string, x, y):
        if x > self.display.width or y > self.display.height or y < 0:
            pass
        for char in range(len(string)):
            byte_data = self._get_bitmap(string[char])
            # print(byte_data)
            if self.reverse:
                for _pixel in range(len(byte_data)):
                    byte_data[_pixel] = ~byte_data[_pixel] & 0xff
            # print(byte_data)
            self.display.blit(framebuf.FrameBuffer(bytearray(byte_data), 16, 16, framebuf.MONO_HLSB), x, y)
            if ord(string[char]) < 128:
                x += 8
            else:
                x += 16

    def show(self):
        self.display.show()
# [
#     "B", "M",  # 标记
#     2,  # 版本
#     0,  # 映射方式
#     0, 0, 0,  # 位图开始字节
#     16,  # 字号
#     0, 0, 0, 0, 0, 0, 0, 0  # 兼容项
# ]
