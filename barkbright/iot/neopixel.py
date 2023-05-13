#!/usr/bin/env python3
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
import re
import time
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
        self._brightness = 1
    
    def set_brightness(self, brightness):
        brightness = min(1, brightness)
        brightness = max(0, brightness)
        self._brightness = brightness

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
    def strip(self):
        return self._current_strip

    def show(self):
        if IS_RPI:
            for i, led in enumerate(self._current_strip):
                color = tuple(led)
                color = tuple([int(self._brightness * c) for c in color])
                self._pixel_strip.setPixelColor(i, Color(*color))
            self._pixel_strip.show()

def light_manager(conn:Connection, run:Value, run_function:Value):
    with NeoPixelLEDStrip(**bb_config['led_config']) as neo_leds:
        while run.value:
            color_func, args = conn.recv()
            run_function.value = True
            if callable(color_func):
                if args:
                    color_func(neo_leds, run_function, *args)
                else:
                    color_func(neo_leds, run_function)

def on(neo_leds:NeoPixelLEDStrip, run_function:Value):
    neo_leds.strip[:] = bb_config['colors']['warm']
    neo_leds.show()

def off(neo_leds:NeoPixelLEDStrip, run_function:Value):
    neo_leds.strip[:] = bb_config['colors']['black']
    neo_leds.show()

def color_change(neo_leds:NeoPixelLEDStrip, run_function:Value, phrase:str):

    for word in phrase.split():
        if word in bb_config['colors']:
            neo_leds.strip[:] = bb_config['colors'][word]
            break
    neo_leds.show()

def increase_brightness(neo_leds:NeoPixelLEDStrip, run_function:Value, phrase:str):
    amount = re.findall(r'\d+\.\d+|\d+', phrase)
    if amount:
        amount = float(amount[0])
        if amount >= 1:
            amount = amount / 100
    else:
        amount = 0.2
    neo_leds.set_brightness(1 + amount)
    neo_leds.show()

def decrease_brightness(neo_leds:NeoPixelLEDStrip, run_function:Value, phrase:str):
    amount = re.findall(r'\d+\.\d+|\d+', phrase)
    if amount:
        amount = float(amount[0])
        if amount >= 1:
            amount = amount / 100
    else:
        amount = 0.2
    neo_leds.set_brightness(1 - amount)
    neo_leds.show()

def party_mode(neo_leds:NeoPixelLEDStrip, run_function:Value):
    party_colors = np.array([
        bb_config['colors']['red'],
        bb_config['colors']['orange'],
        bb_config['colors']['yellow'],
        bb_config['colors']['lime'],
        bb_config['colors']['cyan'],
        bb_config['colors']['blue'],
        bb_config['colors']['purple'],
    ])
    n_tiles = neo_leds.strip.shape[0] // party_colors.shape[0]
    remainder = neo_leds.strip.shape[0] % party_colors.shape[0]
    party_colors = np.concatenate([np.tile(party_colors, (n_tiles, 1)), party_colors[:remainder, :]])
    i = 0
    while run_function.value:
        neo_leds.strip[:] = party_colors
        party_colors = np.roll(party_colors, i, axis=0)
        time.sleep(0.1)
        i = (i + 1) % party_colors.shape[0]
        neo_leds.show()

def sunset_mode(neo_leds:NeoPixelLEDStrip, run_function:Value):
    sunset_colors = np.array([
        bb_config['colors']['yellow'],
        bb_config['colors']['red'],
        bb_config['colors']['orange'],
        bb_config['colors']['pink'],
        bb_config['colors']['purple'],
    ])
    n_tiles = neo_leds.strip.shape[0] // sunset_colors.shape[0]
    remainder = neo_leds.strip.shape[0] % sunset_colors.shape[0]
    sunset_colors = np.concatenate([np.tile(sunset_colors, (n_tiles, 1)), sunset_colors[:remainder, :]])
    sig = 50
    mu = 0
    x = np.linspace(-100, 100, sunset_colors.shape[0])
    gaussian = np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.))) + 1
    gaussian = gaussian[:, np.newaxis]
    gaussian = gaussian / np.max(gaussian)
    i = 0
    while run_function.value:
        neo_leds.strip[:] = np.floor(sunset_colors * gaussian)
        neo_leds.show()
        sunset_colors = np.roll(sunset_colors, i, axis=0)
        i = (i + 1) % sunset_colors.shape[0]
        time.sleep(0.1)
