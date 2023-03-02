# Micropython μFont

Micropython 的字体模块，可以用来显示所有`Unicode`字符。

## 硬件要求

1. 运行`micropython`的开发板，且`micropython>=1.17`
2. 使用`SSD1306`驱动芯片的`OLED屏幕`或者是`ST7735`驱动芯片的`LCD`屏幕亦或是`1.54英寸的e-Paper`
    (只要是使用`FrameBuffer`的屏幕都支持，但本项目提供的驱动只有这三种)
3. 如果想要在`OLED`或者`e-Paper`上使用`ufont`显示支持`GB2312`的所有字符，则至少 `230Kbyte` 的空闲 ROM 空间和 `20 Kbyte`的空闲内存
    如果想要在`ST7735`上使用`ufont`显示支持`GB2312`的所有字符，则至少 `230Kbyte` 的空闲 ROM 空间和 `100 Kbyte`的空闲内存

## 快速上手

1. 准备运行`micropython`的开发板和一个`SSD1306`的`OLED`屏幕，并完成连接

2. 将`demo/ssd1306_demo.py`用编辑器打开

    ```python
    # 修改为对应的 Pin 
    i2c = I2C(scl=Pin(2), sda=Pin(3)) # Line 29
    ```

3. 依次将`demo/ssd1306_demo.py`、`driver/ssd1306.py`、`ufont.py`、`unifont-14-12917-16.v3.bmf`上传到**开发板根目录**，运行`ssd1306_demo.py`即可

## 使用方法

仅需三步就能使用`ufont`:

```python
# 第一步：导入 ufont 库
import ufont
···
# 第二步：加载字体
font = ufont.BMFont("unifont-14-12917-16.v3.bmf")
···
# 第三步：显示文字
font.text(display, "你好", 48, 16, show=True)
```

### 详细参数

```python
text(display, # 显示对象 
     string: str, # 显示文字
     x: int, # 字符串左上角 x 轴
     y: int, # 字符串左上角 y 轴
		 color: int = 0xFFFF, # 字体颜色(RGB565)
     bg_color: int = 0, # 字体背景颜色(RGB565)
     font_size: int = None, # 字号大小
     half_char: bool = True, # 半宽显示 ASCII 字符
     auto_wrap: bool = False, # 自动换行
     show: bool = True, # 实时显示
     clear: bool = False, # 清除之前显示内容
     alpha_color: bool = 0, # 透明色(RGB565) 当颜色与 alpha_color 相同时则透明
     reverse: bool = False, # 逆置(MONO)
     color_type: int = -1, # 色彩模式 0:MONO 1:RGB565
     line_spacing: int = 0, # 行间距
     **kwargs)
```



## 示例程序

1. `SSD1306`演示程序

    ```python
    """
    SSD1306(OLED 128*64) 屏幕中文测试
    Micropython版本: 1.19.1
    演示硬件:
        SSD1306(OLED 128*64 IIC)
        合宙ESP32C3(without ch343)
    所需文件:
        ufont.py
        unifont-14-12917-16.v3.bmf
        ssd1306.py
    链接引脚:
        SCL = 2
        SDA = 3
    使用字体: unifont-14-12917-16.v3.bmf
    """
    import random
    import time
    
    from machine import I2C, Pin
    
    import ufont
    import ssd1306
    
    
    def wait(info, _t=5):
        print(info)
        time.sleep(_t)
    
    
    i2c = I2C(scl=Pin(2), sda=Pin(3))
    display = ssd1306.SSD1306_I2C(128, 64, i2c)
    
    # 载入字体
    #   使用字体制作工具：https://github.com/AntonVanke/MicroPython_BitMap_Tools
    font = ufont.BMFont("unifont-14-12917-16.v3.bmf")
    
    wait("""
    # 最简单的显示 "你好"
    #   其中指定 `show=True` 使得屏幕及时更新
    """, 6)
    font.text(display, "你好", 0, 0, show=True)
    
    wait("""
    # 如果想让文字显示在屏幕正中间，可以通过指定文本左上角位置来修改显示位置
    """, 5)
    font.text(display, "你好", 48, 16, show=True)
    
    wait("""
    # 此时你会发现：上一次显示显示的文字不会消失。因为你没有指定清屏参数：`clear=True`;让我们再试一次
    #   注意，请使用修改后的 `ssd1306.py` 驱动，否则请自行调用`display.fill(0)`
    """, 10)
    font.text(display, "你好", 48, 16, show=True, clear=True)
    
    wait("""
    # 显示英文呢？
    """, 3)
    font.text(display, "He110", 48, 8, show=True, clear=True)
    font.text(display, "你好", 48, 24, show=True)
    
    wait("""
    # 会发现一个汉字的宽度大概是字母的两倍，如果你需要等宽，可以指定参数 `half_char=False`
    """, 6)
    font.text(display, "HELLO", 32, 16, show=True, clear=True, half_char=False)
    
    wait("""
    # 显示的文字如果很长，会超出屏幕边界，例如：
    """, 3)
    poem = "他日若遂凌云志，敢笑黄巢不丈夫!"
    font.text(display, poem, 0, 8, show=True, clear=True)
    
    wait("""
    # 此时，需要指定参数 `auto_wrap=True` 来自动换行
    """, 5)
    font.text(display, poem, 0, 8, show=True, clear=True, auto_wrap=True)
    
    wait("""
    # 自动换行的行间距太小了？
    #   添加 `line_spacing: int` 参数来调整行间距, 此处指定 8 个像素
    """, 8)
    font.text(display, poem, 0, 8, show=True, clear=True, auto_wrap=True, line_spacing=8)
    
    wait("""
    # 调整字体大小，可以指定 `font_size: int` 参数
    #   注意：这会严重增加运行时间
    """, 8)
    font.text(display, "T:" + str(random.randint(-40, 40)) + "℃", 24, 8, font_size=32, show=True, clear=True)
    
    wait("""
    # 当你使用墨水屏时，颜色可能会出现反转。或者你主动想要颜色反转
    #   可以指定参数 `reverse=Ture`
    """, 8)
    font.text(display, "T:" + str(random.randint(-40, 40)) + "℃", 24, 8, font_size=32, show=True, clear=True, reverse=True)
    
    ```

    

2. `ST7735`演示程序

    ```python
    """
    ST7735(LCD 160*80) 屏幕中文测试
    Micropython版本: 1.19.1
    演示硬件:
        合宙 Air10x 系列屏幕扩展板
        合宙ESP32C3(without ch343)
    所需文件:
        ufont.py
        unifont-14-12917-16.v3.bmf
        st7735.py
    链接引脚:
        SCL = 2
        SDA = 3
        RST = 10
        DC  = 6
        CS  = 7
        BL  = 11
    使用字体: unifont-14-12917-16.v3.bmf
    """
    import random
    import time
    
    from machine import SPI, Pin
    
    import ufont
    from st7735 import ST7735
    
    spi = SPI(1, 30000000, sck=Pin(2), mosi=Pin(3))
    display = ST7735(spi=spi, cs=7, dc=6, rst=10, bl=11, width=160, height=80, rotate=1)
    
    
    def wait(info, _t=5):
        print(info)
        time.sleep(_t)
    
    
    # 载入字体
    #   使用字体制作工具：https://github.com/AntonVanke/MicroPython_BitMap_Tools
    font = ufont.BMFont("unifont-14-12917-16.v3.bmf")
    
    wait("""
    # 最简单的显示 "你好"
    #   其中指定 `show=True` 使得屏幕及时更新
    """, 6)
    font.text(display, "你好", 0, 0, show=True)
    
    wait("""
    # 如果想让文字显示在屏幕正中间，可以通过指定文本左上角位置来修改显示位置
    """, 5)
    font.text(display, "你好", 64, 32, show=True)
    
    wait("""
    # 此时你会发现：上一次显示显示的文字不会消失。因为你没有指定清屏参数：`clear=True`;让我们再试一次
    """, 6)
    font.text(display, "你好", 64, 32, show=True, clear=True)
    
    wait("""
    # 显示英文呢？
    """, 3)
    font.text(display, "He110", 64, 26, show=True, clear=True)
    font.text(display, "你好", 64, 42, show=True)
    
    wait("""
    # 会发现一个汉字的宽度大概是字母的两倍，如果你需要等宽，可以指定参数 `half_char=False`
    """, 6)
    font.text(display, "HELLO", 48, 24, show=True, clear=True, half_char=False)
    
    wait("""
    # 可以通过指定参数 `color` 来指定字体颜色，其中 color 是 RGB565 格式
    """, 6)
    font.text(display, "hello", 48, 32, color=0xff00, show=True)
    
    wait("""
    # 同样，我们可以通过指定 `bg_color` 参数调整背景颜色
    """)
    font.text(display, "你好", 56, 28, color=0xff00, bg_color=0x00ff, show=True)
    
    wait("""
    # 大一点？可以使用 `font_size` 指定字号大小
    #   注意：放大彩色字体对内存的要求十分巨大
    """)
    font.text(display, "Temp: 15℃", 0, 26, font_size=32, color=0xff00, bg_color=0x00ff, show=True, clear=True)
    
    ```

    

## 字体制作工具

#### GITHUB

[MicroPython-uFont-Tools/如何生成点阵字体文件.md at master · AntonVanke/MicroPython-uFont-Tools · GitHub](https://github.com/AntonVanke/MicroPython-uFont-Tools/blob/master/doc/如何生成点阵字体文件.md)

#### GITEE

[MicroPython-uFont-Tools: MicroPython uFont 工具 (gitee.com)](https://gitee.com/liio/MicroPython-uFont-Tools)

## 更多信息

#### VIDEOS:

1. [MicroPython中文字库教程_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV12B4y1B7Ff/)
2. [MicroPython中文字库：自定义字体生成_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1YD4y16739/)

#### GITEE:

[MicroPython-Chinese-Font: MicroPython 的中文字库，使 MicroPython 能够显示中文 当然，不止能够显示中文，还可以显示所有 Unicode 字符 (gitee.com)](https://gitee.com/liio/MicroPython-Chinese-Font)

[MicroPython-uFont-Tools: MicroPython uFont 工具 (gitee.com)](https://gitee.com/liio/MicroPython-uFont-Tools)

