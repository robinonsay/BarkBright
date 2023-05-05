#!/usr/bin/env python3
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
from barkbright import bb_config
import time
IS_RPI = bb_config['device'] == 'rpi'
if IS_RPI:
    from rpi_ws281x import PixelStrip, Color

# LED strip configuration:
LED_COUNT = 16       # Number of LED pixels.
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

class NeoPixelLEDStrip:

    def __init__(self, count, pin=18, freq_hz=800000, dma=10, brightness=255, invert=False, channel=0):
        self._count = count
        self._pin = pin
        self._freq_hz = freq_hz
        self._dma = dma
        self._brightness = brightness
        self._invert = invert
        self._channel = channel
        self._pixel_strip = None
    
    def __enter__(self):
        if IS_RPI:
            self._pixel_strip = PixelStrip(self._count, self._pin, self._freq_hz, self._dma, self._invert, self._brightness, self._channel)
            self._pixel_strip.begin()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if IS_RPI:
            for i in range(self._count):
                self._pixel_strip.setPixelColor(i, Color(0,0,0))
            self._pixel_strip.show()

    def __getitem__(self, index):
        pass

    def __setitem__(self, index, value):
        if IS_RPI:
            if isinstance(index, slice):
                for i in index.indices(self._count):
                    self._pixel_strip.setPixelColor(i, Color(*value))
            else:
                self._pixel_strip.setPixelColor(index, Color(*value))
            self._pixel_strip.show()
