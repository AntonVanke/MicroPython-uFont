__version__ = 3

import math
import timeit

import numpy as np


def list_to_bin(arr):
    for _ in range(len(arr)):
        b = []
        for i in range(7, -1, -1):
            b.append(arr[_] >> i & 1)
        arr[_] = b
    return np.asarray(arr).reshape((-1, 16))


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

    def text(self, display, string, x, y, font_size=None, reverse=False):
        """
        显示文字
        :param display: 继承 FrameBuffer 的显示驱动类
        :param string: 字符串
        :param x: x 轴偏移
        :param y: y 轴偏移
        :param font_size: 字号
        :param reverse: 位反转
        :return:
        """
        if font_size is None:
            font_size = self.font_size

        initial_x = x
        if x > display.width or y > display.height or y < 0:
            pass

        for char in range(len(string)):
            # 回车
            if string[char] == '\n':
                y += font_size
                x = initial_x
                continue
            # Tab
            elif string[char] == '\t':
                x = ((x // font_size) + 1) * font_size + initial_x
                continue
            # 其它的控制字符
            elif ord(string[char]) < 16:
                continue
            byte_data = self.get_bitmap(string[char])
            if font_size != self.font_size:
                byte_data = bit_to_byte(zoom(byte_to_bit(byte_data, self.font_size), font_size))
            if reverse:
                for _pixel in range(len(byte_data)):
                    byte_data[_pixel] = ~byte_data[_pixel] & 0xff
            show_bitmap(byte_to_bit(byte_data, font_size=font_size))
            # display.blit(
            #     framebuf.FrameBuffer(bytearray(byte_data), font_size, font_size, framebuf.MONO_HLSB), x, y)



if __name__ == '__main__':
    a = BMFont("unifont-14-12886-16.v3.bmf")
    print(timeit.timeit(lambda: a.get_bitmap("O"), number=1000))
    a.text(None, "OK", 0, 0, font_size=48, reverse=True)
