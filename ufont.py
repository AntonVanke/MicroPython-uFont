#   Github: https://github.com/AntonVanke/MicroPython-uFont
#   Gitee: https://gitee.com/liio/MicroPython-uFont
#   Tools: https://github.com/AntonVanke/MicroPython-ufont-Tools
#   Videos:
#       https://www.bilibili.com/video/BV12B4y1B7Ff/
#       https://www.bilibili.com/video/BV1YD4y16739/
__version__ = 3

import time
import struct

import framebuf

DEBUG = False


def timeit(func, *args, **kwargs):
    """测试函数运行时间"""
    # 当交叉编译后无法获取函数名
    try:
        _name = func.__name__
    except AttributeError:
        _name = "Unknown"

    def get_running_time(*args, **kwargs):
        if DEBUG:
            t = time.ticks_us()
            result = func(*args, **kwargs)
            delta = time.ticks_diff(time.ticks_us(), t)
            print('Function {} Time = {:6.3f}ms'.format(_name, delta / 1000))
            return result
        else:
            return func(*args, **kwargs)

    return get_running_time


class BMFont:
    @timeit
    def text(self, display, string: str, x: int, y: int,
             color: int = 0xFFFF, bg_color: int = 0, font_size: int = None,
             half_char: bool = True, auto_wrap: bool = False, show: bool = True, clear: bool = False,
             alpha_color: bool = 0, reverse: bool = False, color_type: int = -1, line_spacing: int = 0, **kwargs):
        """
        Args:
            display: 显示对象
            string: 显示文字
            x: 字符串左上角 x 轴
            y: 字符串左上角 y 轴
            color: 字体颜色(RGB565)
            bg_color: 字体背景颜色(RGB565)
            font_size: 字号大小
            half_char: 半宽显示 ASCII 字符
            auto_wrap: 自动换行
            show: 实时显示
            clear: 清除之前显示内容
            alpha_color: 透明色(RGB565) 当颜色与 alpha_color 相同时则透明
            reverse: 逆置(MONO)
            color_type: 色彩模式 0:MONO 1:RGB565
            line_spacing: 行间距
            **kwargs:

        Returns:
        MoreInfo: https://github.com/AntonVanke/MicroPython-uFont/blob/master/README.md
        """
        # 如果没有指定字号则使用默认字号
        font_size = font_size or self.font_size
        # 记录初始的 x 位置
        initial_x = x

        # 设置颜色类型
        if color_type == -1 and (display.width * display.height) > len(display.buffer):
            color_type = 0
        elif color_type == -1 or color_type == 1:
            palette = [[bg_color & 0xFF, (bg_color & 0xFF00) >> 8], [color & 0xFF, (color & 0xFF00) >> 8]]
            color_type = 1

        # 处理黑白屏幕的背景反转问题
        if color_type == 0 and color == 0 != bg_color or color_type == 0 and reverse:
            reverse = True
            alpha_color = -1
        else:
            reverse = False

        # 清屏
        try:
            display.clear() if clear else 0
        except AttributeError:
            print("请自行调用 display.fill() 清屏")

        for char in range(len(string)):
            if auto_wrap and ((x + font_size // 2 > display.width and ord(string[char]) < 128 and half_char) or
                              (x + font_size > display.width and (not half_char or ord(string[char]) > 128))):
                y += font_size + line_spacing
                x = initial_x

            # 对控制字符的处理
            if string[char] == '\n':
                y += font_size + line_spacing
                x = initial_x
                continue
            elif string[char] == '\t':
                x = ((x // font_size) + 1) * font_size + initial_x % font_size
                continue
            elif ord(string[char]) < 16:
                continue

            # 超过范围的字符不会显示*
            if x > display.width or y > display.height:
                continue

            # 获取字体的点阵数据
            byte_data = list(self.get_bitmap(string[char]))

            # 分四种情况逐个优化
            #   1. 黑白屏幕/无放缩
            #   2. 黑白屏幕/放缩
            #   3. 彩色屏幕/无放缩
            #   4. 彩色屏幕/放缩
            if color_type == 0:
                byte_data = self._reverse_byte_data(byte_data) if reverse else byte_data
                if font_size == self.font_size:
                    display.blit(framebuf.FrameBuffer(bytearray(byte_data), font_size, font_size, framebuf.MONO_HLSB),
                                 x, y,
                                 alpha_color)
                else:
                    display.blit(
                        framebuf.FrameBuffer(self._HLSB_font_size(byte_data, font_size, self.font_size), font_size,
                                             font_size, framebuf.MONO_HLSB), x, y, alpha_color)
            elif color_type == 1 and font_size == self.font_size:
                display.blit(framebuf.FrameBuffer(self._flatten_byte_data(byte_data, palette), font_size, font_size,
                                                  framebuf.RGB565), x, y, alpha_color)
            elif color_type == 1 and font_size != self.font_size:
                display.blit(framebuf.FrameBuffer(self._RGB565_font_size(byte_data, font_size, palette, self.font_size),
                                                  font_size, font_size, framebuf.RGB565), x, y, alpha_color)
            # 英文字符半格显示
            if ord(string[char]) < 128 and half_char:
                x += font_size // 2
            else:
                x += font_size

        display.show() if show else 0

    @timeit
    def _get_index(self, word: str) -> int:
        """
        获取索引
        Args:
            word: 字符

        Returns:
        ESP32-C3: Function _get_index Time =  2.670ms
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
    def _HLSB_font_size(self, byte_data: bytearray, new_size: int, old_size: int) -> bytearray:
        old_size = old_size
        _temp = bytearray(new_size * ((new_size >> 3) + 1))
        _new_index = -1
        for _col in range(new_size):
            for _row in range(new_size):
                if (_row % 8) == 0:
                    _new_index += 1
                _old_index = int(_col / (new_size / old_size)) * old_size + int(_row / (new_size / old_size))
                _temp[_new_index] = _temp[_new_index] | (
                        (byte_data[_old_index >> 3] >> (7 - _old_index % 8) & 1) << (7 - _row % 8))
        return _temp

    @timeit
    def _RGB565_font_size(self, byte_data: bytearray, new_size: int, palette: list, old_size: int) -> bytearray:
        old_size = old_size
        _temp = []
        _new_index = -1
        for _col in range(new_size):
            for _row in range(new_size):
                if (_row % 8) == 0:
                    _new_index += 1
                _old_index = int(_col / (new_size / old_size)) * old_size + int(_row / (new_size / old_size))
                _temp.extend(palette[byte_data[_old_index // 8] >> (7 - _old_index % 8) & 1])
        return bytearray(_temp)

    @timeit
    def _flatten_byte_data(self, _byte_data: bytearray, palette: list) -> bytearray:
        """
        渲染彩色像素
        Args:
            _byte_data:
            palette:

        Returns:

        """
        _temp = []
        for _byte in _byte_data:
            for _b in range(7, -1, -1):
                _temp.extend(palette[(_byte >> _b) & 0x01])
        return bytearray(_temp)

    @timeit
    def _reverse_byte_data(self, _byte_data: bytearray) -> bytearray:
        for _pixel in range(len(_byte_data)):
            _byte_data[_pixel] = ~_byte_data[_pixel] & 0xff
        return _byte_data

    @timeit
    def get_bitmap(self, word: str) -> bytes:
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
        #   字体文件信息大小 16 byte ,按照顺序依次是
        #       文件标识 2 byte
        #       版本号 1 byte
        #       映射方式 1 byte
        #       位图开始字节 3 byte
        #       字号 1 byte
        #       单字点阵字节大小 1 byte
        #       保留 7 byte
        self.bmf_info = self.font.read(16)

        # 判断字体是否正确
        #   文件头和常用的图像格式 BMP 相同，需要添加版本验证来辅助验证
        if self.bmf_info[0:2] != b"BM":
            raise TypeError("字体文件格式不正确: " + font_file)
        self.version = self.bmf_info[2]
        if self.version != 3:
            raise TypeError("字体文件版本不正确: " + str(self.version))

        # 映射方式
        #   目前映射方式并没有加以验证，原因是 MONO_HLSB 最易于处理
        self.map_mode = self.bmf_info[3]

        # 位图开始字节
        #   位图数据位于文件尾，需要通过位图开始字节来确定字体数据实际位置
        self.start_bitmap = struct.unpack(">I", b'\x00' + self.bmf_info[4:7])[0]
        # 字体大小
        #   默认的文字字号，用于缩放方面的处理
        self.font_size = self.bmf_info[7]
        # 点阵所占字节
        #   用来定位字体数据位置
        self.bitmap_size = self.bmf_info[8]
