import timeit

import numpy as np


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


class BMFont:
    @staticmethod
    def bytes_to_int(byte):
        i = 0
        for _ in byte:
            i = (i << 8) + _

        return i

    def __init__(self, font_file, reverse=False):
        self.reverse = reverse
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
        self.font.seek(self.start_bitmap + self._get_index(word) * self.bitmap_size, 0)
        return list(self.font.read(self.bitmap_size))


if __name__ == '__main__':
    a = BMFont("unifont-14-12886-16.v3.bmf")
    print(timeit.timeit(lambda: a.get_bitmap("我"), number=1000))

    show_bitmap(list_to_bin(a.get_bitmap("我")))
