# coding: utf-8
"""Applet manager"""
from time import sleep
import datetime
import timeit
import threading
import logging
import PIL.Image as Img
import g19d.libdraw as libdraw
from g19d.logitech.g19 import G19
from g19d.logitech.g19_keys import Key
from g19d.coloradapter import ColorAdapter
from g19d.appmgr.keybindings import KeyBindings
from g19d.apps.watch import Watch
from g19d.apps.notify import Notification
import os
import sys



class AppMgr(object):
    """docstring for AppMgr."""
    def __init__(self):
        fmat = u'%(levelname)-8s [%(asctime)s] <%(funcName)s:%(lineno)s> %(message)s'
        fname = "/var/log/g19d/{}.log".format(os.environ.get("USER", "unknown"))
        logging.basicConfig(format=fmat, filename=fname, level=logging.DEBUG)
        super(AppMgr, self).__init__()
        self.__exit = threading.Event()
        self.__lcd = G19(True)
        self.__key_listener = KeyBindings(self.__lcd)
        self.__lcd.add_key_listener(self.__key_listener)
        self.__lcd.start_event_handling()
        self.__color_adapter = ColorAdapter(self.ambient_callback)
        self.__apps = [Watch(self), Notification(self)]
        self.__cur_app = self.__apps[0]
        self.__prev_app = self.__cur_app
        self.__key_listener.register_keybind(self.__cur_app.get_keybind())
        self.__color_adapter.start()

        logging.info(u'AppMgr has been inited')

    def run(self):
        """Routine for applet manager"""
        for app in self.__apps:
            app.run()

        while not self.__exit.is_set():
            start_time = timeit.default_timer()
            frame = self.__cur_app.get_frame_data()
            if not frame:
                continue
            self.__lcd.send_frame(frame)
            cooldown = (self.__cur_app.get_interval() - (timeit.default_timer() - start_time))
            if cooldown < 0:
                logging.info("Cooldown is negative")
                cooldown = 0.001
            sleep(cooldown)

    def ambient_callback(self, color_rgb):
        """Callback for ColorAdapter"""
        self.__lcd.set_bg_color(color_rgb[0], color_rgb[1], color_rgb[2])
        for app in self.__apps:
            app.ambient_callback(color_rgb)

    def shutdown(self, *args):
        """Shutdown appmgr"""
        logging.debug(u'Shutting down...')
        if self.__exit.is_set():
            logging.warn(u'Already shutting')
            return
        self.__exit.set()

        for app in self.__apps:
            app.shutdown()

        logging.debug(u'Color adapter...')
        self.__color_adapter.shutdown()
        self.__color_adapter.join()

        logging.debug(u'Lcd reset...')

        self.__lcd.stop_event_handling()
        self.__lcd.reset()

        logging.info(u'Success shutdown!')

    def irq(self, app):
        self.unirq()
        self.__prev_app = self.__cur_app
        self.__cur_app = app
        self.__key_listener.register_keybind(self.__cur_app.get_keybind())

    def unirq(self):
        self.__cur_app = self.__prev_app
        self.__key_listener.register_keybind(self.__cur_app.get_keybind())
