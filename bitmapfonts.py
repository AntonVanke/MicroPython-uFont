__version__ = 3

# 生成点阵字体文件
import struct
import numpy as np
from PIL import ImageFont, ImageDraw, Image

"""
#
# 配置
# 
"""
OFFSET = (0, 0)  # 字体偏移
CHAR_SET_FILE = "text.txt"  # 字体集
FONT_SIZE = 16  # 字号
FONT_FILE = "unifont-14.0.04.ttf"  # 字体文件


def get_im(word, width, height, offset: tuple = OFFSET) -> Image.Image:
    """
    获取生成的图像
    :param word: 字
    :param width: 宽度
    :param height: 高度
    :param offset: 偏移
    :return:
        :type: PIL.Image.Image
    """
    im = Image.new('1', (width, height), (1,))
    draw = ImageDraw.Draw(im)
    draw.text(offset, word, font=FONT)
    return im


def to_bitmap(word: str) -> bytearray:
    code = 0x00
    data_code = word.encode("utf-8")

    # 获取字节码
    try:
        for byte in range(len(data_code)):
            code |= data_code[byte] << (len(data_code) - byte - 1) * 8
    except IndexError:
        print(word, word.encode("utf-8"))

    # 获取点阵图
    bp = np.pad((~np.asarray(get_im(word, width=FONT_SIZE, height=FONT_SIZE))).astype(np.int32),
                ((0, 0), (0, int(np.ceil(FONT_SIZE / 8) * 8 - FONT_SIZE))), 'constant', constant_values=(0, 0))

    # 点阵映射 MONO_HLSB
    bmf = []
    for line in bp.reshape((-1, 8)):
        v = 0x00
        for _ in line:
            v = (v << 1) + _
        bmf.append(v)
    return bytearray(bmf)


def get_unicode(word) -> bytes:
    """
    返回 Unicode 编码
    :param word:
    :return:
    """
    return struct.pack(">H", ord(word))


if __name__ == '__main__':
    # 获取文字并排序
    WORDS = list(set(list(open(CHAR_SET_FILE, encoding="utf-8").read())))
    WORDS.sort()
    FONT_NUM = len(WORDS)
    FONT = ImageFont.truetype(font=FONT_FILE, size=FONT_SIZE)

    # 生成的点阵字体文件
    bitmap_fonts = open(FONT_FILE.split('.')[0] + "-" + str(FONT_NUM) + "-" + str(FONT_SIZE) + ".v3.bmf", "wb")

    # 字节记录占位
    bitmap_fonts.write(bytearray([
        66, 77,  # 标记
        3,  # 版本
        0,  # 映射方式
        0, 0, 0,  # 位图开始字节
        FONT_SIZE,  # 字号
        int(np.ceil(FONT_SIZE / 8)) * FONT_SIZE,  # 每个字占用的大小
        0, 0, 0, 0, 0, 0, 0  # 兼容项
    ]))

    for w in WORDS:
        bitmap_fonts.write(get_unicode(w))

    # 位图开始字节
    start_bitmap = bitmap_fonts.tell()

    for w in WORDS:
        bitmap_fonts.write(to_bitmap(w))

    bitmap_fonts.seek(4, 0)
    bitmap_fonts.write(struct.pack(">i", start_bitmap)[1:4])
