import datetime
import timeit
import os
import logging
from time import sleep
import configparser
import threading
import random

from g19d.apps import Applet
import PIL.Image as Img
import g19d.libdraw as libdraw
from g19d.logitech.g19_keys import Key

class Watch(Applet):
    """docstring for Watch."""
    __DEFAULT_BACKGROUND_PATH = os.path.dirname(os.path.abspath(__file__)) + "/../background.png"

    def __init__(self, appmgr):
        super(Watch, self).__init__(appmgr)
        self.name = "Watch"
        self.__load_config()

        self.__background = Img.open(self.__background_path)
        self.__background = self.__background.resize((320, 240), Img.CUBIC)
        self.__background_crop = self.__background.crop((0, 90, 320, 175))

        self.__timer = Watch.get_time
        self.__time_offset = datetime.datetime.now()
        self.__freeze_delta = datetime.timedelta(0, 0, 0)
        self.__freeze_time = None
        self.__freeze_flag = False

        self.__watch_alpha = 0.6
        self.__bg_color = [177, 31, 80, self.__watch_alpha]

        self.__need_startup = threading.Event()

    def __load_config(self):
        self.__background_path = self.__DEFAULT_BACKGROUND_PATH
        background_path = self._get_config("background")

        if background_path and os.access(background_path, os.R_OK):
            self.__background_path = background_path

        snow_enable = self._get_config("snow_flakes")
        if snow_enable == "yes":
            self.__snow = Img.open(os.path.dirname(os.path.abspath(__file__)) + "/../flake.png")
            self.__snow_pos = []
            while len(self.__snow_pos) < 50:
                self.__snow_pos.append([random.randint(-10, 330), random.randint(-10, 250)])
        else:
            self.__snow = False

    def _startup(self):
        """Draw init image on screen"""
        drawer = self._drawer
        time = datetime.datetime.now().strftime("%H:%M:%S")

        drawer.draw_image([0, 0], [320, 240], self.__background)
        drawer.draw_rectangle([0, 90], [320, 85], self.__bg_color)
        drawer.draw_textline([32, 90], 72, time)

    def get_keybind(self):
        def reset_timer(key, state):
            self.__time_offset = datetime.datetime.now()
            self.__freeze_delta = datetime.timedelta(0, 0, 0)
            if self.__freeze_flag:
                self.__freeze_time = datetime.datetime.now()

        def pause(key, state):
            if self.__freeze_flag:
                self.__freeze_delta += datetime.datetime.now() - self.__freeze_time
                self.__freeze_time = None
                self.__freeze_flag = False
            else:
                self.__freeze_time = datetime.datetime.now()
                self.__freeze_flag = True

        def switch(key, state):
            if self.__timer == Watch.get_time:
                self.__timer = self.__stopwatch
            else:
                self.__timer = Watch.get_time

        return { (Key.BACK, True): reset_timer,
                 (Key.MENU, True): switch,
                 (Key.OK, True):   pause }

    def _loop(self):
        while not self._exit.is_set():
            start_time = timeit.default_timer()
            self.__routine()
            self._save_frame_data()
            cooldown = (0.1 - (timeit.default_timer() - start_time))
            if cooldown < 0:
                print("cooldown is negative!")
                cooldown = 0.001
            self._exit.wait(timeout=cooldown)

    def __routine(self):
        """Applet's routine"""
        if self.__need_startup.is_set():
            self.__need_startup.clear()
            self._startup()

        drawer = self._drawer
        time = self.__timer()

        if self.__snow:
            background = self.__background
            flake_img = self.__snow

            drawer.draw_image([0, 0], [320, 240], background)
            for flake in self.__snow_pos:
                flake[0] = flake[0] + random.randint(-1, 1)
                flake[1] = flake[1] + random.randint(1, 5)
                if flake[0] > 330:
                    flake[0] = flake[0] % 25 * -1
                if flake[1] > 250:
                    flake[1] = flake[1] % 25 * -1
                if flake[0] < -10:
                    flake[0] = flake[0] % 25 + 310
                if flake[1] < -10:
                    flake[1] = flake[1] % 25 + 230
                drawer.draw_image(flake, [25, 25], flake_img)
        else:
            background_crop = self.__background_crop
            drawer.draw_image([0, 90], [320, 85], background_crop)

        drawer.draw_rectangle([0, 90], [320, 85], self.__bg_color)
        drawer.draw_textline([32, 103], 72, time)

    def ambient_callback(self, color_rgb):
        """Callback for ambient_light"""
        if color_rgb == [0, 0, 0]:
            return
        self.__bg_color = color_rgb + [ self.__watch_alpha ]

    def __stopwatch(self):
        if self.__freeze_time:
            curtime = self.__freeze_time
        else:
            curtime = datetime.datetime.now()

        return (datetime.datetime.min + (curtime - self.__time_offset - self.__freeze_delta)).time().strftime("%H:%M:%S")

    @staticmethod
    def get_time():
        return datetime.datetime.now().strftime("%H:%M:%S")

    def update_config(self):
        self.__load_config()
        self.__background = Img.open(self.__background_path)
        self.__background = self.__background.resize((320, 240), Img.CUBIC)
        self.__background_crop = self.__background.crop((0, 90, 320, 175))
        self.__need_startup.set()

