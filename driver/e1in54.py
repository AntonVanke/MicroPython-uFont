# 来源：QQ群786510434、https://github.com/mcauser/micropython-waveshare-epaper/blob/master/epaper1in54.py
from micropython import const
from time import sleep_ms
import ustruct
from machine import Pin
import framebuf

# Display resolution
EPD_WIDTH = const(200)
EPD_HEIGHT = const(200)

# Display commands
DRIVER_OUTPUT_CONTROL = const(0x01)
BOOSTER_SOFT_START_CONTROL = const(0x0C)
# GATE_SCAN_START_POSITION             = const(0x0F)
DEEP_SLEEP_MODE = const(0x10)
DATA_ENTRY_MODE_SETTING = const(0x11)
# SW_RESET                             = const(0x12)
# TEMPERATURE_SENSOR_CONTROL           = const(0x1A)
MASTER_ACTIVATION = const(0x20)
# DISPLAY_UPDATE_CONTROL_1             = const(0x21)
DISPLAY_UPDATE_CONTROL_2 = const(0x22)
WRITE_RAM = const(0x24)
WRITE_VCOM_REGISTER = const(0x2C)
WRITE_LUT_REGISTER = const(0x32)
SET_DUMMY_LINE_PERIOD = const(0x3A)
SET_GATE_TIME = const(0x3B)  # not in datasheet
# BORDER_WAVEFORM_CONTROL              = const(0x3C)
SET_RAM_X_ADDRESS_START_END_POSITION = const(0x44)
SET_RAM_Y_ADDRESS_START_END_POSITION = const(0x45)
SET_RAM_X_ADDRESS_COUNTER = const(0x4E)
SET_RAM_Y_ADDRESS_COUNTER = const(0x4F)
TERMINATE_FRAME_READ_WRITE = const(0xFF)  # aka NOOP


class EPD(framebuf.FrameBuffer):
    LUT_FULL_UPDATE = bytearray(
        b'\x02\x02\x01\x11\x12\x12\x22\x22\x66\x69\x69\x59\x58\x99\x99\x88\x00\x00\x00\x00\xF8\xB4\x13\x51\x35\x51\x51\x19\x01\x00')
    LUT_PARTIAL_UPDATE = bytearray(
        b'\x10\x18\x18\x08\x18\x18\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x13\x14\x44\x12\x00\x00\x00\x00\x00\x00')

    def __init__(self, spi, cs, dc, rst, busy):
        self.spi = spi
        self.cs = Pin(cs, Pin.OUT, value=1)
        self.dc = Pin(dc, Pin.OUT, value=0)
        self.rst = Pin(rst, Pin.OUT, value=0)
        self.busy = Pin(busy, Pin.IN)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.pages = self.height // 8
        self.buffer = bytearray(self.width * self.pages)
        super().__init__(self.buffer, self.width, self.height,
                         framebuf.MONO_HLSB)
        self.init()

    def clear(self):
        self.buffer = (b'\xff' * self.width * self.pages)

    def show(self):
        self.set_frame_memory(self.buffer, 0, 0, 200, 200)
        self.display_frame()

    def _command(self, command, data=None):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(command.to_bytes(1, 'big'))
        # self.spi.write(bytearray([command]))
        self.cs.value(1)
        if data is not None:
            self._data(data)

    def _data(self, data):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(data)
        self.cs.value(1)

    def init(self):
        self.reset()
        self._command(DRIVER_OUTPUT_CONTROL)
        self._data(bytearray([(EPD_HEIGHT - 1) & 0xFF]))
        self._data(bytearray([((EPD_HEIGHT - 1) >> 8) & 0xFF]))
        self._data(bytearray([0x00]))  # GD = 0 SM = 0 TB = 0
        self._command(BOOSTER_SOFT_START_CONTROL, b'\xD7\xD6\x9D')
        self._command(WRITE_VCOM_REGISTER, b'\xA8')  # VCOM 7C
        self._command(SET_DUMMY_LINE_PERIOD, b'\x1A')  # 4 dummy lines per gate
        self._command(SET_GATE_TIME, b'\x08')  # 2us per line
        self._command(DATA_ENTRY_MODE_SETTING, b'\x03')  # X increment Y increment
        # self._command(DATA_ENTRY_MODE_SETTING, b'\x07') # X increment Y increment
        self.set_lut(self.LUT_FULL_UPDATE)

    def wait_until_idle(self):
        while self.busy.value() == 1:
            sleep_ms(100)

    def reset(self):
        self.rst.value(0)
        sleep_ms(200)
        self.rst.value(1)
        sleep_ms(200)

    def set_lut(self, lut):
        self._command(WRITE_LUT_REGISTER, lut)

    # put an image in the frame memory
    def set_frame_memory(self, image, x, y, w, h):
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        x = x & 0xF8
        w = w & 0xF8

        if x + w >= self.width:
            x_end = self.width - 1
        else:
            x_end = x + w - 1

        if y + h >= self.height:
            y_end = self.height - 1
        else:
            y_end = y + h - 1

        self.set_memory_area(x, y, x_end, y_end)
        self.set_memory_pointer(x, y)
        self._command(WRITE_RAM, image)

    # replace the frame memory with the specified color
    def clear_frame_memory(self, color):
        self.set_memory_area(0, 0, self.width - 1, self.height - 1)
        self.set_memory_pointer(0, 0)
        self._command(WRITE_RAM)
        # send the color data
        for i in range(0, self.width // 8 * self.height):
            # self._data(bytearray([color]))
            self._data(bytearray(color))

    # draw the current frame memory and switch to the next memory area
    def display_frame(self):
        self._command(DISPLAY_UPDATE_CONTROL_2, b'\xC4')
        self._command(MASTER_ACTIVATION)
        self._command(TERMINATE_FRAME_READ_WRITE)
        self.wait_until_idle()

    # specify the memory area for data R/W
    def set_memory_area(self, x_start, y_start, x_end, y_end):
        self._command(SET_RAM_X_ADDRESS_START_END_POSITION)
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self._data(bytearray([(x_start >> 3) & 0xFF]))
        self._data(bytearray([(x_end >> 3) & 0xFF]))
        self._command(SET_RAM_Y_ADDRESS_START_END_POSITION, ustruct.pack("<HH", y_start, y_end))

    # specify the start point for data R/W
    def set_memory_pointer(self, x, y):
        self._command(SET_RAM_X_ADDRESS_COUNTER)
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self._data(bytearray([(x >> 3) & 0xFF]))
        self._command(SET_RAM_Y_ADDRESS_COUNTER, ustruct.pack("<H", y))
        self.wait_until_idle()

    # to wake call reset() or init()
    def sleep(self):
        self._command(DEEP_SLEEP_MODE, b'\x01')  # enter deep sleep A0=1, A0=0 power on
        self.wait_until_idle()

    def set_refresh(self, full_update=True):
        self.set_lut(self.LUT_FULL_UPDATE) if full_update else self.set_lut(self.LUT_PARTIAL_UPDATE)
