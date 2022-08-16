__version__ = 3

import math
import struct

import framebuf


def rgb(r, g, b):
    """
    RGB255 to RGB565
    :param r:
    :param g:
    :param b:
    :return:
    """
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def hrgb(h):
    """
    hex(RGB225) to RGB565
    :param h:
    :return:
    """
    return (((h >> 16 & 0xff) & 0xF8) << 8) | (((h >> 8 & 0xff) & 0xFC) << 3) | ((h & 0xff) >> 3)


def reshape(bitarray):
    """
    改成 n * 8 列表
    :param bitarray:
    :return:
    """
    for _ in range(len(bitarray)):
        bitarray[_].extend([0 for i in range(math.ceil(len(bitarray[_]) / 8) * 8 - len(bitarray[_]))])
    arr = []
    for _c in range(len(bitarray)):
        for _r in range(0, len(bitarray[_c]), 8):
            arr.append(bitarray[_c][_r:_r + 8])
    return arr


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


def byte_to_bit(byte_arr, font_size):
    """
    :param byte_arr:
    :param font_size:
    :return:
    """
    temp2_arr = []
    for _ in range(len(byte_arr)):
        temp_arr = []
        for i in range(7, -1, -1):
            temp_arr.append(byte_arr[_] >> i & 1)
        temp2_arr.extend(temp_arr)
    bit_arr = []
    for _ in range(0, len(temp2_arr), font_size):
        bit_arr.append(temp2_arr[_: _ + font_size])
    return bit_arr


def bit_to_byte(bitarray):
    """
    位图数组转字节
    :param bitarray: 位图数组
    :return:
    """
    bmf = []
    for line in reshape(bitarray):
        v = 0x00
        for _ in line:
            v = (v << 1) + _
        bmf.append(v)
    return bytearray(bmf)


def zoom(bitarray, font_size):
    """
    点阵放大
    :param bitarray: 位图数组
    :param font_size: 放大字号
    :return:
    """
    a_height = len(bitarray)
    a_width = len(bitarray[0])
    new_bitarray = [[0 for j in range(font_size)] for i in range(font_size)]
    for _col in range(len(new_bitarray)):
        for _row in range(len(new_bitarray[_col])):
            new_bitarray[_col][_row] = bitarray[int(_col / (font_size / a_height))][int(_row / (font_size / a_width))]
    return new_bitarray


class BMFont:
    @staticmethod
    def bytes_to_int(byte):
        i = 0
        for _ in byte:
            i = (i << 8) + _

        return i

    @staticmethod
    def clear(display, fill):
        """
        清空缓冲区
        :param fill: 填充像素
        :param display: 继承 FrameBuf 的显示驱动对象
        :return:
        """
        display.fill(fill)

    def __init__(self, font_file):
        self.font_file = font_file

        self.font = open(font_file, "rb", buffering=0xff)

        self.bmf_info = self.font.read(16)

        if self.bmf_info[0:2] != b"BM":
            raise TypeError("字体文件格式不正确: " + font_file)

        self.version = self.bmf_info[2]
        if self.version != 3:
            raise TypeError("字体文件版本不正确: " + str(self.version))

        self.map_mode = self.bmf_info[3]
        self.start_bitmap = self.bytes_to_int(self.bmf_info[4:7])
        self.font_size = self.bmf_info[7]
        self.bitmap_size = self.bmf_info[8]

    def _get_index(self, word):
        """
        获取索引
        :param word:
        :return:
        """
        word_code = ord(word)
        start = 0x10
        end = self.start_bitmap

        while start <= end:
            mid = ((start + end) // 4) * 2
            self.font.seek(mid, 0)
            target_code = self.bytes_to_int(self.font.read(2))
            if word_code == target_code:
                return (mid - 16) >> 1
            elif word_code < target_code:
                end = mid - 2
            else:
                start = mid + 2
        return -1

    def get_bitmap(self, word):
        """
        获取点阵图
        :param word: 字
        :return:
        """
        index = self._get_index(word)
        if index == -1:
            return [255, 255, 255, 255, 255, 255, 255, 255, 240, 15, 207, 243, 207, 243, 255, 243, 255, 207, 255, 63,
                    255, 63, 255, 255, 255, 63, 255, 63, 255, 255, 255, 255]
        self.font.seek(self.start_bitmap + index * self.bitmap_size, 0)
        return list(self.font.read(self.bitmap_size))

    @staticmethod
    def _with_color(bitarray, _color):
        color_array = b''
        for _col in range(len(bitarray)):
            for _row in range(len(bitarray)):
                if bitarray[_col][_row] == 1:
                    color_array += struct.pack("<H", _color)
                else:
                    color_array += struct.pack("<H", 0)
        return color_array

    def text(self, display, string, x=0, y=0, color=1, font_size=None, reverse=False, clear=False, show=False,
             half_char=True, *args, **kwargs):
        """
        显示文字
        :param half_char: 英文是否半格显示
        :param color: 文字颜色
        :param display: 继承 FrameBuffer 的显示驱动类
        :param string: 字符串
        :param x: x 轴偏移
        :param y: y 轴偏移
        :param font_size: 字号
        :param reverse: 位反转
        :param show: 是否立即显示
        :param clear: 显示前清屏
        :return:
        """
        # 如果没有给定 font_size ，使用字体默认大小
        if font_size is None:
            font_size = self.font_size

        if clear:
            self.clear(display, reverse)
        initial_x = x

        for char in range(len(string)):
            # 回车
            if string[char] == '\n':
                y += font_size
                x = initial_x
                continue
            # Tab
            elif string[char] == '\t':
                x = ((x // font_size) + 1) * font_size + initial_x % font_size
                continue

            # 其它的控制字符不显示
            elif ord(string[char]) < 16:
                continue

            # 超过范围的字符不会显示
            if x > display.width or y > display.height:
                continue

            byte_data = self.get_bitmap(string[char])
            if font_size != self.font_size:
                byte_data = bit_to_byte(zoom(byte_to_bit(byte_data, self.font_size), font_size))
            if reverse:
                for _pixel in range(len(byte_data)):
                    byte_data[_pixel] = ~byte_data[_pixel] & 0xff

            # 黑白屏
            if color in [1, 0]:
                display.blit(
                    framebuf.FrameBuffer(bytearray(byte_data), font_size, font_size, framebuf.MONO_HLSB), x, y)
            else:
                byte_data = self._with_color(byte_to_bit(byte_data, math.ceil(font_size / 8) * 8), color)
                display.blit(
                    framebuf.FrameBuffer(bytearray(byte_data), font_size, font_size, framebuf.RGB565), x, y)
            if ord(string[char]) < 128 and half_char:
                x += font_size // 2
            else:
                x += font_size
        if show:
            display.show()
