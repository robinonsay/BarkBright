#!/usr/bin/env python3
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
import numpy as np
from barkbright import bb_config
from multiprocessing.connection import Connection
from multiprocessing import Process, Pipe, Value
IS_RPI = bb_config['device'] == 'rpi'
if IS_RPI:
    from rpi_ws281x import PixelStrip, Color

class NeoPixelLEDStrip:

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._pixel_strip = None
        self._current_strip = np.zeros((self._kwargs['count'], 3))
    
    def __enter__(self):
        if IS_RPI:
            self._pixel_strip = PixelStrip(self._kwargs["count"],
                                           self._kwargs["gpio"],
                                           self._kwargs["freq_hz"],
                                           self._kwargs["dma"],
                                           self._kwargs["invert"],
                                           self._kwargs["brightness"],
                                           self._kwargs["channel"])
            self._pixel_strip.begin()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if IS_RPI:
            for i in range(self._kwargs["count"]):
                self._pixel_strip.setPixelColor(i, Color(0,0,0))
            self._pixel_strip.show()
    
    def __len__(self):
        return self._kwargs['count']
    
    @property
    def leds(self):
        return self._current_strip

    def show(self):
        if IS_RPI:
            for i, led in enumerate(self._current_strip):
                color = tuple(led)
                color = tuple([int(c) for c in color])
                self._pixel_strip.setPixelColor(i, Color(*color))
            self._pixel_strip.show()

def light_manager(conn:Connection, run:Value, run_function:Value):
    with NeoPixelLEDStrip(**bb_config['led_config']) as leds:
        while run.value:
            colors = conn.recv()
            if isinstance(colors, np.ndarray):
                leds.leds[:] = colors
                leds.show()
            elif callable(colors):
                colors(leds, run_function)
                run_function.value = True
