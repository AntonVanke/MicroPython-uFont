__version__ = 3

import time
import struct

import framebuf

DEBUG = False


def timeit(f, *args, **kwargs):
    try:
        myname = str(f).split(' ')[1]
    except:
        myname = "UNKONW"

    def new_func(*args, **kwargs):
        if DEBUG:
            try:
                t = time.ticks_us()
                result = f(*args, **kwargs)
                delta = time.ticks_diff(time.ticks_us(), t)
                print('Function {} Time = {:6.3f}ms'.format(myname, delta / 1000))
            except AttributeError:
                t = time.perf_counter_ns()
                result = f(*args, **kwargs)
                delta = time.perf_counter_ns() - t
                print('Function {} Time = {:6.3f}ms'.format(myname, delta / 1000000))
            return result
        else:
            return f(*args, **kwargs)

    return new_func


class BMFont:
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
    def __init__(self, font_file):
        self.font_file = font_file

        self.font = open(font_file, "rb", buffering=0xff)

        self.bmf_info = self.font.read(16)

        if self.bmf_info[0:2] != b"BM":
            raise TypeError("字体文件格式不正确: " + font_file)

        self.version = self.bmf_info[2]
        if self.version != 3:
            raise TypeError("字体文件版本不正确: " + str(self.version))

        self.map_mode = self.bmf_info[3]  # 映射方式
        self.start_bitmap = struct.unpack(">I", b'\x00' + self.bmf_info[4:7])[0]  # 位图开始字节
        self.font_size = self.bmf_info[7]  # 字体大小
        self.bitmap_size = self.bmf_info[8]  # 点阵所占字节

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
    def _color_render(self, bit_list, color):
        """将二值点阵图像转换为 RGB565 彩色字节图像

        Args:
            bit_list:
            color:

        Returns:

        """
        color_array = b""
        for _col in range(len(bit_list)):
            for _row in range(len(bit_list)):
                color_array += struct.pack("<H", color) if bit_list[_col][_row] else b'\x00\x00'
        return color_array

    @timeit
    def _get_index(self, word):
        """获取索引

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
    def text(self, display, string, x, y, color=1, *, font_size=None, reverse=False, clear=False, show=False,
             half_char=True, auto_wrap=False, **kwargs):
        """通过显示屏显示文字

        使用此函数显示文字，必须先确认显示对象是否继承与 framebuf.FrameBuffer。
        如果显示对象没有 clear 方法，需要自行调用 fill 清屏

        Args:
            display: 显示实例
            string: 字符串
            x: 字体左上角 x 轴
            y: 字体左上角 y 轴
            color: 颜色
            font_size: 字号
            reverse: 是否反转背景
            clear: 是否清除之前显示的内容
            show: 是否立刻显示
            half_char: 是否半字节显示 ASCII 字符
            auto_wrap: 自动换行
            **kwargs:

        Returns:
            None
        """
        font_size = font_size or self.font_size
        initial_x = x

        # 清屏
        try:
            display.clear() if clear else 0
        except AttributeError:
            print("请自行调用 display.fill(*) 清屏")

        for char in range(len(string)):
            # 是否自动换行
            if auto_wrap:
                if auto_wrap and ((x + font_size // 2 >= display.width and ord(string[char]) < 128 and half_char) or
                                  (x + font_size >= display.width and (not half_char or ord(string[char]) > 128))):
                    y += font_size
                    x = initial_x

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

            # 超过范围的字符不会显示*
            if x > display.width or y > display.height:
                continue

            byte_data = list(self.get_bitmap(string[char]))

            # 反转
            if reverse:
                for _pixel in range(len(byte_data)):
                    byte_data[_pixel] = ~byte_data[_pixel] & 0xff

            # 缩放和色彩*
            if color > 1 or font_size != self.font_size:
                bit_data = self._to_bit_list(byte_data, font_size)
                if color > 1:
                    display.blit(
                        framebuf.FrameBuffer(bytearray(self._color_render(bit_data, color)), font_size, font_size,
                                             framebuf.RGB565), x, y)
                else:
                    display.blit(
                        framebuf.FrameBuffer(bytearray(self._bit_list_to_byte_data(bit_data)), font_size, font_size,
                                             framebuf.MONO_HLSB), x, y)
            else:
                display.blit(framebuf.FrameBuffer(bytearray(byte_data), font_size, font_size, framebuf.MONO_HLSB), x, y)

            # 英文字符半格显示
            if ord(string[char]) < 128 and half_char:
                x += font_size // 2
            else:
                x += font_size

        display.show() if show else 0

    def char(self, char, color=1, font_size=None, reverse=False):
        """ 获取字体字节数据

        在没有继承 framebuf.FrameBuffer 的显示驱动,或者内存不足以将一整个屏幕载入缓存帧时
        可以直接获取单字的字节数据,局部更新
        Args:
            char: 单个字符
            color: 颜色
            font_size: 字体大小
            reverse: 反转

        Returns:
            bytearray
        """
        font_size = font_size or self.font_size
        byte_data = list(self.get_bitmap(char))

        # 反转
        if reverse:
            for _pixel in range(len(byte_data)):
                byte_data[_pixel] = ~byte_data[_pixel] & 0xff
        if color > 1 or font_size != self.font_size:
            bit_data = self._to_bit_list(byte_data, font_size)
            if color > 1:
                return self._color_render(bit_data, color)
            else:
                return self._bit_list_to_byte_data(bit_data)
        else:
            return bytearray(byte_data)


if __name__ == '__main__':
    def show_bitmap(arr):
        """
        显示点阵字 MONO_HLSB
        :return:
        """
        for row in arr:
            for i in row:
                if i:
                    print('* ', end=' ')
                else:
                    print('. ', end=' ')
            print()


    font = BMFont("unifont-14-12888-16.v3.bmf")
    print("16 ----")
    bd = font.char("我", reverse=True, color=0xffff, font_size=16)
    print("24 ----")
    bd = font.char("我", reverse=True, color=0xffff, font_size=24)
    print("16 ----")
    # font._with_color(zoom(byte_to_bit(font.get_bitmap("我"), 16), 24), 0xff00)
    font._color_render(font._to_bit_list(font.get_bitmap("我"), 24), 0xff00)
