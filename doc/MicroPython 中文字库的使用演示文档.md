## MicroPython 中文字库[ufont]的使用

Github: https://github.com/AntonVanke/MicroPython-Chinese-Font

#### 使用方法

以【合宙 Air10x 系列屏幕扩展板驱动】为例

1. 如何确认驱动是否支持？

   ```python
   from st7735 import ST7735
   from framebuf import FrameBuffer
   print(issubclass(ST7735, FrameBuffer)) # True: 支持;False: 不支持
   ```

   如果返回的是`True`则支持，`False`的话需要一些额外的操作

2. 先初始化屏幕

   ```python
   from machine import SPI, Pin
   from st7735 import ST7735, color
   spi = SPI(1, 30000000, sck=Pin(2), mosi=Pin(3))
   display = ST7735(spi=spi, cs=18, dc=12, rst=1, bl=19, width=160, height=80, rotate=1)
   ```

3. 载入字体

   - 上传`ufont.py`、`unifont-14-12888-16.v3.bmf`到开发板

   ```python
   import ufont
   f = ufont.BMFont("../unifont-14-12888-16.v3.bmf")
   ```

4. 测试字体

   1. 基本使用

      - `text(显示实例，文字，x轴，y轴，颜色 )`

      - `show = True` 立即显示，就不需要执行 `display.show() `

      ```python
      f.text(display, "你好", 0, 0, color=0xf8, show=True)
      ```

   2. 如何设置字号

      ```python
      f.text(display, "你好", 32, 0, color=0xe007, font_size=18, show=True)
      ```

   3. 如何显示反转背景的字体

      ```python
      f.text(display, "你好", 68, 0, color=0xe007, reverse=True, show=True)
      ```

   4. 如何显示的时候清除之前的内容

      ```python
      f.text(display, "你好\nabCD123", 0, 0,font_size=16, color=0xf8, clear=True, show=True)
      ```

   5. 当某些字体需要全格显示时

      - `half_char=False` 英文数字全格显示

      ```python
      f2 = ufont.BMFont("DIGITAL-Dreamfat-95-16.v3.bmf")  # 载入特殊字体
      f2.text(display, "abCD123", 0, 32,font_size=16, color=0xe007,half_char=False,show=True)
      ```