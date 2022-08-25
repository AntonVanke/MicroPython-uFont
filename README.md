# MicroPython-Chinese

MicroPython 的中文显示模块，使其可以在显示模块上显示汉字。此外也可以自定义字体集，使其能够满足不同存储空间、不同语言的要求。

### 资源

[MicroPython中文字库教程](https://www.bilibili.com/video/BV12B4y1B7Ff/)

[MicroPython 中文字库的使用演示文档](/doc/MicroPython%20中文字库的使用演示文档.md)

[如何生成点阵字体文件](/doc/如何生成点阵字体文件.md)

### 简单上手

所需

1. 运行 `micropython` 的开发板
2. 使用 `SSD1306 驱动芯片`的 `OLED 128*64` 屏幕
3. 拥有至少 `512Kbyte` 的空闲 ROM 空间和 `20 Kbyte`的空闲内存

**两步操作**

1. 将 `demo/ssd1306_demo.py`文件修改为你所连接的引脚

   ```python
   i2c = I2C(scl=Pin(2), sda=Pin(3))  # line 16
   ```

2. 依次将`demo/ssd1306_demo.py`、`driver/ssd1306.py`、`ufont.py`、`unifont-14-12888-16.v3.bmf`上传到**开发板根目录**，运行`ssd1306_demo.py`即可

图片

如果你运行成功了，正常情况下是会显示

   <img src="https://s1.ax1x.com/2022/07/31/vFBplT.jpg" alt="运行效果" style="zoom: 33%;" />

### 使用方法

**项目文件**

```shell
.
├── LICENSE
├── README.md
├── bitmapfonts.py  # 点阵字体生成
├── demo
│   ├── epaper1in54_demo.py  # 1.54 英寸墨水屏例子
│   ├── ssd1306_demo.py  # 0.96 英寸 OLED 例子
│   └── st7735_demo.py  # 合宙 Air10x 系列屏幕扩展板驱动 例子(不完善)
├── doc
│   ├── MicroPython 中文字库的使用演示文档.md
│   └── 如何生成点阵字体文件.md
├── driver
│   ├── e1in54.py  # 1.54 英寸墨水屏驱动
│   ├── ssd1306.py  # 0.96 英寸 OLED 驱动
│   └── st7735.py  # 合宙 Air10x 系列屏幕扩展板驱动
├── requirements.txt  # python 库需求文件
├── text.txt  # 默认字体集，用于生成点阵字体，可以自定义文字
├── ufont.py  # ⭐库文件
├── unifont-14-12888-16.v3.bmf  # ⭐生成的点阵字体
└── unifont-14.0.04.ttf  # Unifont 字体 https://savannah.gnu.org/projects/unifont/
```

上传`ufont.py`、`unifont-14-12888-16.v3.bmf`到`MicroPython`根目录

**对于**`SSD1306(OLED 128*64)`

```python
from machine import Pin, I2C

import ssd1306
import ufont

i2c = I2C(scl=Pin(2), sda=Pin(3))  # 定义 I2C 管脚
display = ssd1306.SSD1306_I2C(128, 64, i2c)  # 驱动对象

f = ufont.BMFont("unifont-14-12888-16.v3.bmf")  # 中文显示对象

f.text(
    display=display,  # 显示对象 必要
    string="",  # 显示的文字 必要
    x=0,  # x 轴
    y=0,  # y 轴
    color=1,  # 颜色 默认是 1(黑白)
    font_size=16, # 字号(像素)
    reverse=False, # 逆置(墨水屏会用到)
    clear=False,  # 显示前清屏
    show=False  # 是否立即显示
)
```

**对于**`st7735(80*160)[合宙 Air10x 系列屏幕扩展板]`

详见[MicroPython 中文字库的使用演示文档](/doc/MicroPython%20中文字库的使用演示文档.md)

### 字体生成

详见[如何生成点阵字体文件](/doc/如何生成点阵字体文件.md)

### 生成的字体文件格式

![点阵字体文件格式](https://s1.ax1x.com/2022/07/31/vkQ9u6.jpg)

### 注意事项

1. 采用`Framebuf`缓冲区的驱动才能够使用
2. 最好全程使用推荐字号(16px)否则会有各种各样的问题
3. 主要缓冲区内存不足的问题(尤其是TFT屏幕)
