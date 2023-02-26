#   Github: https://github.com/AntonVanke/MicroPython-Chinese-Font
#   Gitee: https://gitee.com/liio/MicroPython-Chinese-Font
#   Tools: https://github.com/AntonVanke/MicroPython_BitMap_Tools
#   Videos:
#       https://www.bilibili.com/video/BV12B4y1B7Ff/
#       https://www.bilibili.com/video/BV1YD4y16739/
__version__ = 3

import time
import struct

import framebuf

DEBUG = False


def timeit(func, *args, **kwargs):
    """
    测试程序时间
    Args:
        func:
        *args:
        **kwargs:

    Returns:

    """

    def get_running_time(*args, **kwargs):
        if DEBUG:
            try:
                t = time.ticks_us()
                result = func(*args, **kwargs)
                delta = time.ticks_diff(time.ticks_us(), t)
                print('Function {} Time = {:6.3f}ms'.format(func.__name__, delta / 1000))
            except AttributeError:
                t = time.perf_counter_ns()
                result = func(*args, **kwargs)
                delta = time.perf_counter_ns() - t
                print('Function {} Time = {:6.3f}ms'.format(func.__name__, delta / 1000000))
            return result
        else:
            return func(*args, **kwargs)

    return get_running_time


class BMFont:
    @timeit
    def text(self, display, string: str, x: int, y: int, color: int = 1, bg_color: int = -1, font_size: int = None,
             half_char: bool = True, auto_wrap: bool = False, show: bool = True, clear=False, alpha_color=-1,
             reverse=False, **kwargs):
        """
        Args:
            display: 显示实例
            string: 字符串
            x: 字体左上角 x 轴
            y: 字体左上角 y 轴
            color: 字体颜色
            bg_color: 背景颜色，当和 alpha_color 相同为 -1 时背景透明
            font_size: 字号
            half_char: 是否半字节显示 ASCII 字符
            auto_wrap: 自动换行
            show: 执行自动更新到屏幕
            clear: 更新前清屏
            alpha_color: 当和 alpha_color 相同为 -1 时背景透明
            reverse: 当使用 epaper 时，指定为 True (通过反转字节来反转背景)
            **kwargs:

        Returns:

        """
        # 如果没有指定字号则使用默认字号
        font_size = font_size or self.font_size
        # 记录初始的 x 位置
        initial_x = x

        # 判断是 RGB565 还是 MONO_HLSB
        if (display.width * display.height) > len(display.buffer):
            color_type = 0
        else:
            color_type = 1
            palette = [[bg_color & 0xFF, (bg_color & 0xFF00) >> 8], [color & 0xFF, (color & 0xFF00) >> 8]]

        try:
            display.clear() if clear else 0
        except AttributeError:
            print("请自行调用 display.fill() 清屏")

        # TODO:设置字体颜色(前景色乱变)
        # palette_buffer = bytearray(8)
        # palette = framebuf.FrameBuffer(palette_buffer, 2, 1, framebuf.RGB565)
        # palette.pixel(0, 0, bg_color)
        # palette.pixel(1, 0, color)

        for char in range(len(string)):
            # 对自动换行的处理
            if auto_wrap:
                if auto_wrap and ((x + font_size // 2 >= display.width and ord(string[char]) < 128 and half_char) or
                                  (x + font_size >= display.width and (not half_char or ord(string[char]) > 128))):
                    y += font_size
                    x = initial_x

            # 对于回车的处理
            if string[char] == '\n':
                y += font_size
                x = initial_x
                continue

            # 对于制表符的处理
            elif string[char] == '\t':
                x = ((x // font_size) + 1) * font_size + initial_x % font_size
                continue

            # 其它的控制字符不显示
            elif ord(string[char]) < 16:
                continue

            # 超过范围的字符不会显示*
            if x > display.width or y > display.height:
                continue

            # 获取字体的点阵数据
            byte_data = list(self.get_bitmap(string[char]))

            if font_size != self.font_size or color_type == 1:
                bit_data = self._to_bit_list(byte_data, font_size)
                if color_type == 1:
                    byte_data = self._flatten_bit_data(bit_data, palette)
                elif color_type == 0:
                    if reverse:
                        for _pixel in range(len(byte_data)):
                            byte_data[_pixel] = ~byte_data[_pixel] & 0xff
                    byte_data = self._bit_list_to_byte_data(bit_data)

            if color_type == 1:
                display.blit(framebuf.FrameBuffer(bytearray(byte_data), font_size, font_size, framebuf.RGB565), x, y,
                             alpha_color)
            elif color_type == 0:
                display.blit(framebuf.FrameBuffer(bytearray(byte_data), font_size, font_size, framebuf.MONO_HLSB), x, y,
                             alpha_color)

            # 英文字符半格显示
            if ord(string[char]) < 128 and half_char:
                x += font_size // 2
            else:
                x += font_size

        display.show() if show else 0

    @timeit
    def _flatten_bit_data(self, _bit_data, palette=None):
        _temp = []
        for row in _bit_data:
            for e in row:
                _temp.extend(palette[e])
        return _temp

    @staticmethod
    def _list_to_byte(arr):
        b = 0
        for a in arr:
            b = (b << 1) + a
        return bytes([b])

    @timeit
    def _bit_list_to_byte_data(self, bit_list):
        """将点阵转换为字节数据

        Args:
            bit_list:

        Returns:

        """
        byte_data = b''
        for _col in bit_list:
            for i in range(0, len(_col), 8):
                byte_data += self._list_to_byte(_col[i:i + 8])
        return byte_data

    @timeit
    def _to_bit_list(self, byte_data, font_size, *, _height=None, _width=None):
        """将字节数据转换为点阵数据

        Args:
            byte_data: 字节数据
            font_size: 字号大小
            _height: 字体原高度
            _width: 字体原宽度

        Returns:

        """
        _height = _height or self.font_size
        _width = _width or self.bitmap_size // self.font_size * 8
        new_bitarray = [[0 for j in range(font_size)] for i in range(font_size)]
        for _col in range(len(new_bitarray)):
            for _row in range(len(new_bitarray[_col])):
                _index = int(_col / (font_size / _height)) * _width + int(_row / (font_size / _width))
                new_bitarray[_col][_row] = byte_data[_index // 8] >> (7 - _index % 8) & 1
        return new_bitarray

    @timeit
    def _get_index(self, word):
        """
        获取索引
        Args:
            word: 字符

        Returns:

        """
        word_code = ord(word)
        start = 0x10
        end = self.start_bitmap

        while start <= end:
            mid = ((start + end) // 4) * 2
            self.font.seek(mid, 0)
            target_code = struct.unpack(">H", self.font.read(2))[0]
            if word_code == target_code:
                return (mid - 16) >> 1
            elif word_code < target_code:
                end = mid - 2
            else:
                start = mid + 2
        return -1

    @timeit
    def get_bitmap(self, word):
        """获取点阵图

        Args:
            word: 字符

        Returns:
            bytes 字符点阵
        """
        index = self._get_index(word)
        if index == -1:
            return b'\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x0f\xcf\xf3\xcf\xf3\xff\xf3\xff\xcf\xff?\xff?\xff\xff\xff' \
                   b'?\xff?\xff\xff\xff\xff'

        self.font.seek(self.start_bitmap + index * self.bitmap_size, 0)
        return self.font.read(self.bitmap_size)

    @timeit
    def __init__(self, font_file):
        """
        Args:
            font_file: 字体文件路径
        """
        self.font_file = font_file
        # 载入字体文件
        self.font = open(font_file, "rb")
        # 获取字体文件信息
        self.bmf_info = self.font.read(16)

        # 判断字体是否正确
        if self.bmf_info[0:2] != b"BM":
            raise TypeError("字体文件格式不正确: " + font_file)

        self.version = self.bmf_info[2]
        if self.version != 3:
            raise TypeError("字体文件版本不正确: " + str(self.version))

        # 映射方式
        self.map_mode = self.bmf_info[3]
        # 位图开始字节
        self.start_bitmap = struct.unpack(">I", b'\x00' + self.bmf_info[4:7])[0]
        # 字体大小
        self.font_size = self.bmf_info[7]
        # 点阵所占字节
        self.bitmap_size = self.bmf_info[8]


if __name__ == '__main__':
    font = BMFont("unifont-14-12888-16.v3.bmf")
    font._get_index("我")
