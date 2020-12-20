import datetime
import timeit
import os
import logging
from time import sleep

from g19d.apps import Applet
import PIL.Image as Img
import g19d.libdraw as libdraw
from g19d.logitech.g19_keys import Key

class Watch(Applet):
    """docstring for Watch."""

    def __init__(self, appmgr):
        super(Watch, self).__init__(appmgr)
        self.name = "Watch"
        self.__background = Img.open(os.path.dirname(os.path.abspath(__file__)) + "/../background.png")
        self.__background = self.__background.resize((320, 240), Img.CUBIC)
        self.__background_crop = self.__background.crop((0, 90, 320, 175))

        self.__timer = Watch.get_time
        self.__time_offset = datetime.datetime.now()
        self.__freeze_delta = datetime.timedelta(0, 0, 0)
        self.__freeze_time = None
        self.__freeze_flag = False

        self.__watch_alpha = 0.6
        self.__bg_color = [177, 31, 80, self.__watch_alpha]

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
            sleep(cooldown)

    def __routine(self):
        """Applet's routine"""
        drawer = self._drawer
        time = self.__timer()

        drawer.draw_image([0, 90], [320, 85], self.__background_crop)
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


