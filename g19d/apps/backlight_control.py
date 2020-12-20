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

class BLctl(Applet):
    """Control backlight color and ambilight"""
    AMBILIGHT = 1
    MANUAL = 2
    MODE_NAMES = {
        AMBILIGHT: "ambient",
        MANUAL: "manual",
    }
    COLORS = {
        0: [255, 0, 0],
        1: [0, 255, 0],
        2: [0, 0, 255],
        3: [0, 0, 0],
        4: [255, 255, 255],
    }

    def __init__(self, appmgr):
        super(BLctl, self).__init__(appmgr)
        self.name = "Backlight control"
        self.__current_mode = BLctl.AMBILIGHT
        self.__current_color = 0
        self.__bg_color = [0, 0, 0]
        self.__entry = "mode"
        self.__changed = threading.Event()

    def _startup(self):
        """Draw init image on screen"""
        drawer = self._drawer
        drawer.draw_rectangle([0, 0], [320, 240], self.__bg_color)
        drawer.draw_rectangle([15, 30], [240, 34], [145, 90, 0])
        drawer.draw_textline([16, 32], 32, "Backlight control", 0xffff)

    def get_keybind(self):
        def change_mode(key):
            if self.__current_mode == BLctl.AMBILIGHT:
                self.__current_mode = BLctl.MANUAL
                self._appmgr.disable_ambient()
                self._appmgr.ambient_callback(BLctl.COLORS[self.__current_color], True)
            elif self.__current_mode == BLctl.MANUAL:
                self.__current_mode = BLctl.AMBILIGHT
                self._appmgr.enable_ambient()

        def change_color(key):
            if self.__current_mode != BLctl.MANUAL:
                return
            if key == Key.LEFT:
                self.__current_color = self.__current_color - 1 \
                                       if self.__current_color > 0 \
                                       else len(BLctl.COLORS) - 1
            elif key == Key.RIGHT:
                self.__current_color = self.__current_color + 1 \
                                       if self.__current_color < len(BLctl.COLORS) - 1 \
                                       else 0
            self._appmgr.ambient_callback(BLctl.COLORS[self.__current_color], True)

        self.__toggle = {
            "mode": change_mode,
            "color": change_color
        }

        def move_trough_list(key, state):
            if self.__current_mode != BLctl.MANUAL:
                return
            if self.__entry == "mode":
                self.__entry = "color"
            elif self.__entry == "color":
                self.__entry = "mode"
            self.__changed.set()

        def change_state(key, state):
            self.__toggle[self.__entry](key)
            self.__changed.set()


        return { (Key.UP, True): move_trough_list,
                 (Key.DOWN, True): move_trough_list,
                 (Key.LEFT, True): change_state,
                 (Key.RIGHT, True): change_state }

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

        mode_name = BLctl.MODE_NAMES[self.__current_mode]
        if self.__entry == "mode":
            drawer.draw_rectangle([30, 80], [240, 20], [0, 0, 155])
            mode_name = "< " + mode_name + " >"
        drawer.draw_textline([31, 81], 18, "Mode:", 0xffff)
        drawer.draw_textline([171, 81], 18, mode_name, 0xffff)

        if self.__current_mode == BLctl.MANUAL:
            if self.__entry == "color":
                drawer.draw_rectangle([30, 110], [240, 20], [0, 0, 155])
                drawer.draw_textline([186, 111], 18, "<     >", 0xffff)
            drawer.draw_textline([31, 111], 18, "Color:", 0xffff)
            drawer.draw_rectangle([200, 113], [14, 14], BLctl.COLORS[self.__current_color])
