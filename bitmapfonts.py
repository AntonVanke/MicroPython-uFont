__version__ = 3
"""
usage: bitmapfonts.py [-h] [-v] -ff FONT_FILE [-tf TEXT_FILE] [-fs FONT_SIZE] [-o [OFFSET ...]] [-bfn BITMAP_FONT_NAME]

生成点阵字体文件

options:
  -h, --help            show this help message and exit
  -v, --version         显示生成的点阵字体版本
  -ff FONT_FILE, --font-file FONT_FILE
                        字体文件
  -tf TEXT_FILE, --text-file TEXT_FILE
                        文字文件
  -fs FONT_SIZE, --font-size FONT_SIZE
                        生成字体字号
  -o [OFFSET ...], --offset [OFFSET ...]
                        生成字体偏移
  -bfn BITMAP_FONT_NAME, --bitmap-font-name BITMAP_FONT_NAME
                        生成的点阵字体文件名称
example:
    python bitmapfonts.py -ff unifont-14.0.04.ttf -tf text.txt -fs 16 -o 0 0 -bfn example.bmf
"""
import struct
import argparse

try:
    import numpy as np
    from PIL import ImageFont, ImageDraw, Image
except ImportError as err:
    print(err, "尝试运行 `python -m pip install requirements.txt`")
    exit()

parser = argparse.ArgumentParser(description="生成点阵字体文件")
group = parser.add_mutually_exclusive_group()
parser.add_argument('-v', '--version', action='version',
                    version=f'点阵字体版本 : {__version__}',
                    help='显示生成的点阵字体版本')
parser.add_argument("-ff", "--font-file", help="字体文件", type=str, required=True)
group.add_argument("-tf", "--text-file", help="文字文件", type=str, default="text.txt")
group.add_argument("-t", "--text", help="生成的文字", type=str)
parser.add_argument("-fs", "--font-size", help="生成字体字号", default=16, type=int)
parser.add_argument("-o", "--offset", nargs="*", help="生成字体偏移", type=int, default=[0, 0])
parser.add_argument("-bfn", "--bitmap-font-name", help="生成的点阵字体文件名称", type=str)
args = parser.parse_args()

FONT = ImageFont.truetype(font=args.font_file, size=args.font_size)

if args.text:
    WORDS = list(set(list(args.text)))
else:
    WORDS = list(set(list(open(args.text_file, encoding="utf-8").read())))
WORDS.sort()
FONT_NUM = len(WORDS)


def get_im(word, width, height, offset: tuple = args.offset) -> Image.Image:
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
    bp = np.pad((~np.asarray(get_im(word, width=args.font_size, height=args.font_size))).astype(np.int32),
                ((0, 0), (0, int(np.ceil(args.font_size / 8) * 8 - args.font_size))), 'constant',
                constant_values=(0, 0))

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


# 生成的点阵字体文件
# print(args)
bitmap_fonts_name = args.bitmap_font_name or args.font_file.split('.')[0] + "-" + str(FONT_NUM) + "-" + str(
    args.font_size) + ".v3.bmf"
bitmap_fonts = open(bitmap_fonts_name, "wb")
print(f"正在生成点阵字体文件，字体数量{FONT_NUM}：")
# 字节记录占位
bitmap_fonts.write(bytearray([
    66, 77,  # 标记
    3,  # 版本
    0,  # 映射方式
    0, 0, 0,  # 位图开始字节
    args.font_size,  # 字号
    int(np.ceil(args.font_size / 8)) * args.font_size,  # 每个字占用的大小
    0, 0, 0, 0, 0, 0, 0  # 兼容项
]))

for w in WORDS:
    bitmap_fonts.write(get_unicode(w))

# 位图开始字节
start_bitmap = bitmap_fonts.tell()
print("\t位图起始字节：", hex(start_bitmap))
for w in WORDS:
    bitmap_fonts.write(to_bitmap(w))
print(f"\t文件大小：{bitmap_fonts.tell() / 1024:.4f}Kbyte")
bitmap_fonts.seek(4, 0)
bitmap_fonts.write(struct.pack(">i", start_bitmap)[1:4])
print(f"生成成功，文件名称：{bitmap_fonts_name}")
