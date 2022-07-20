# 生成点阵字体文件
import numpy as np
from PIL import ImageFont, ImageDraw, Image

# 需要转换的字符集并排序
WORDS = list(set(list(open("7000.txt", encoding="utf-8").read())))
WORDS.sort()
# open("7000.txt", "w", encoding="utf-8").write("".join(WORDS))
# print(WORDS)
# 字体偏移， 不同字体生成可能会有偏移
OFFSET = (0, -5)
# 转换为点阵文件的源字体文件
FONT_SIZE = 16
FONT = ImageFont.truetype(font='SourceHanSansSC-Light.otf', size=FONT_SIZE)

# 生成的 bmf
bitmap_fonts = open("SourceHanSansSC-Light.bmf", "wb")


def get_im(word, width, height, offset: tuple = OFFSET):
    im = Image.new('1', (width, height), (1,))
    draw = ImageDraw.Draw(im)
    draw.text(offset, word, font=FONT)
    return im


def to_bitmap(word):
    code = 0x00
    data_code = word.encode("utf-8")
    width = FONT_SIZE
    # fixme: 如果英文为 8 宽度无法存储
    # if ord(word) < 128:
    #     width = 8
    # else:
    #     width = 16
    try:
        for byte in range(len(data_code)):
            code |= data_code[byte] << (len(data_code) - byte - 1) * 8
    except IndexError:
        print(word, word.encode("utf-8"))

    bp = (~np.asarray(get_im(word, width=width, height=FONT_SIZE))).astype(np.int32)

    bmf = []

    for line in bp.reshape((-1, 8)):
        v = 0x00
        for _ in line:
            v = (v << 1) + _
        bmf.append(v)
    # print(bp)
    # for b in bp:
    #     v = 0
    #     for _ in b[0:8]:
    #         v = (v << 1) + _
    #     bmf.append(v)
    # #
    # for e in bp:
    #     v = 0
    #     for _ in e[8:]:
    #         v = (v << 1) + _
    #     bmf.append(v)

    bitmap_fonts.write(bytearray(bmf))


# 字节记录占位
bitmap_fonts.write(bytearray([0x01, 0, 0, 0, FONT_SIZE, 0, 0, 0, 0]))  # 第一位存 bmf 版本，中间三位存开始位置，第五位存字号

for _ in WORDS:
    bitmap_fonts.write(bytearray(_.encode("utf-8")))

print("索引写入完毕", bitmap_fonts.tell(), hex(bitmap_fonts.tell()))
start_bitmap = bitmap_fonts.tell()

# 点阵开始字节写入
bitmap_fonts.seek(0x01, 0)
bitmap_fonts.write(bytearray([start_bitmap >> 16, (start_bitmap & 0xff00) >> 8, start_bitmap & 0xff]))
bitmap_fonts.seek(start_bitmap, 0)

# 开始写入点阵
for _ in WORDS:
    to_bitmap(_)

print("点阵写入完毕", bitmap_fonts.tell(), hex(bitmap_fonts.tell()))
bitmap_fonts.close()
