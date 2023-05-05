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

class NeoPixelLEDStrip:

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._pixel_strip = None
    
    def __enter__(self):
        if IS_RPI:
            self._pixel_strip = PixelStrip(self._kwargs["count"],
                                           self._kwargs["gpio"],
                                           self._kwargs["freq_hz"],
                                           self._kwargs["dma"],
                                           self._kwargs["invert"],
                                           self._kwargs["brightness"],
                                           self._kwargs["channel": 0])
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
