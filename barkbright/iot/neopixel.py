#!/usr/bin/env python3
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.

import time
from rpi_ws281x import PixelStrip, Color
import argparse

# LED strip configuration:
LED_COUNT = 100       # Number of LED pixels.
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
        self._pixel_strip = PixelStrip(self._count, self._pin, self._freq_hz, self._dma, self._invert, self._brightness, self._channel)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for i in range(self._pixel_strip.numPixels()):
            self._pixel_strip.setPixelColor(i, Color(0,0,0))
        self._pixel_strip.show()

    def __getitem__(self, index):
        pass

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            for i in range(index.start, index.stop, index.step):
                self._pixel_strip.setPixelColor(i, value)
        else:
            self._pixel_strip.setPixelColor(index, value)
        self._pixel_strip.show()
