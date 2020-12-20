import datetime
import timeit
import os
import logging
from time import sleep
import threading

from g19d.apps import Applet
import PIL.Image as Img
import g19d.libdraw as libdraw
from g19d import libcdraw
from g19d.logitech.g19_keys import Key

class AList(Applet):
    """docstring for Applet."""
    LISTED = 0
    def __init__(self, appmgr):
        super(AList, self).__init__(appmgr)
        self.name = "Applets list"
        self.__bg_color = [0, 0, 0]
        self.__entry = 0
        self.__changed = threading.Event()
        self.__apps = ()

    def _startup(self):
        """Draw init image on screen"""
        drawer = self._drawer
        drawer.draw_rectangle([0, 0], [320, 240], self.__bg_color)
        drawer.draw_rectangle([15, 30], [240, 34], [145, 90, 0])
        drawer.draw_textline([16, 32], 32, "Applets list", 0xffff)

    def _loop(self):
        while not self._exit.is_set():
            start_time = timeit.default_timer()

            if not self.__changed:
                sleep(0.05)
                continue
            self.__changed.clear()

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
        drawer.draw_rectangle([0, 80], [320, 120], self.__bg_color)

        margin = 0
        for key, app in enumerate(self.__apps):
            pos_y = 80 + margin
            margin += 30
            if self.__entry == key:
                drawer.draw_rectangle([30, pos_y], [240, 30], [0, 0, 155])
            drawer.draw_textline([31, pos_y + 1], 24, app.name, 0xffff)

    def get_keybind(self):
        self.__apps = tuple(app for app in self._appmgr.get_apps_list() if app.LISTED)

        def irq(key, state):
            self._appmgr.irq(self)
        def move_trough_list(key, state):
            if key == Key.UP:
                self.__entry = self.__entry - 1 \
                                       if self.__entry > 0 \
                                       else len(self.__apps) - 1
            elif key == Key.DOWN:
                self.__entry = self.__entry + 1 \
                                       if self.__entry < len(self.__apps) - 1 \
                                       else 0
            self.__changed.set()

        def change_app(key, state):
            self._appmgr.change_app(self.__apps[self.__entry])

        return { (Key.UP, True): move_trough_list,
                 (Key.DOWN, True): move_trough_list,
                 (Key.OK, True): change_app }

    def get_keybind_irq(self):
        def irq(key, state):
            self._appmgr.irq(self)

        return { (Key.SETTINGS, True): irq }


if __name__ == '__main__':
    exit(1)
