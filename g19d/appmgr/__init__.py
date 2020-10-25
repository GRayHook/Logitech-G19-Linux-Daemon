# coding: utf-8
"""Applet manager"""
from time import sleep
import datetime
import timeit
import threading
import logging
from gi.repository import GLib
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import PIL.Image as Img
import g19d.libdraw as libdraw
from g19d.logitech.g19 import G19
from g19d.logitech.g19_keys import Key
from g19d.coloradapter import ColorAdapter
from g19d.appmgr.keybindings import KeyBindings
import os
import sys



class AppMgr(object):
    """docstring for AppMgr."""
    def __init__(self):
        fmat = u'%(levelname)-8s [%(asctime)s] <%(funcName)s:%(lineno)s> %(message)s'
        fname = "/var/log/g19d/{}.log".format(os.environ.get("USER", "unknown"))
        logging.basicConfig(format=fmat, filename=fname, level=logging.DEBUG)
        super(AppMgr, self).__init__()
        DBusGMainLoop(set_as_default=True)
        self.__lock = threading.Lock()
        self.__exit = threading.Event()
        self.__lcd = G19(True)
        self.__key_listener = KeyBindings(self.__lcd)
        self.__lcd.add_key_listener(self.__key_listener)
        self.__lcd.start_event_handling()
        self.__drawer = libdraw.Drawer()
        self.__color_adapter = ColorAdapter(self.ambient_callback)
        self.__cur_app = UrPidor(self.__drawer)
        self.__key_listener.register_keybind(self.__cur_app.get_keybind())
        self.__color_adapter.start()
        self.__notification_loop = GLib.MainLoop()
        self.__notification_thread = threading.Thread(target=self.__notification_thread_target,
                                                      name='Notification thread')
        self.__notification_thread.start()

        logging.info(u'AppMgr has been inited')

    def __notification_thread_target(self):
        if self.__exit.wait(timeout=10):
            return
        session_bus = dbus.SessionBus()
        session_bus.add_match_string_non_blocking(
            "eavesdrop=true, interface='org.freedesktop.Notifications', member='Notify'")
        session_bus.add_message_filter(self.__print_notification)
        session_bus.call_on_disconnection(self.shutdown)
        self.__notification_loop.run()

    def __print_notification(self, bus, message):
        if self.__exit.is_set():
            return
        keys = ["app_name", "replaces_id", "app_icon", "summary",
                "body", "actions", "hints", "expire_timeout"]
        args = message.get_args_list()
        if len(args) == 8:
            notification = dict([(keys[i], args[i]) for i in range(8)])
            drawer = libdraw.Drawer()
            notification_app = Notification(drawer, notification)
            notification_app.startup()

            self.__lock.acquire()
            self.__lcd.send_frame(drawer.get_frame_data())
            timeout = notification["expire_timeout"] / 1000 \
                      if 2000 <= notification["expire_timeout"] <= 10000 \
                      else 4
            self.__exit.wait(timeout=timeout)
            self.__lock.release()

    def routine(self):
        """Routine for applet manager"""
        self.__cur_app.startup()
        while True:
            self.__lock.acquire()
            if self.__exit.is_set():
                self.__lock.release()
                break
            self.__cur_app.routine()
            start_time = timeit.default_timer()
            self.__lcd.send_frame(self.__drawer.get_frame_data())
            self.__lock.release()
            cooldown = (self.__cur_app.get_cd() - (timeit.default_timer() - start_time))
            if cooldown < 0:
                logging.info("Cooldown is negative")
                cooldown = 0.01
            sleep(cooldown)

    def ambient_callback(self, color_rgb):
        """Callback for ColorAdapter"""
        self.__lcd.set_bg_color(color_rgb[0], color_rgb[1], color_rgb[2])
        self.__cur_app.ambient_callback(color_rgb)

    def set_exit(self):
        self.__exit.set()

    def shutdown(self, *args):
        """Shutdown appmgr"""
        logging.debug(u'Shutting down...')
        if self.__exit.is_set():
            logging.warn(u'Already shutting')
            return
        self.__exit.set()

        logging.debug(u'Notify loop...')
        if self.__notification_loop.is_running():
            self.__notification_loop.quit()
        self.__notification_thread.join()

        logging.debug(u'Color adapter...')
        self.__color_adapter.shutdown()
        self.__color_adapter.join()

        logging.debug(u'Lcd reset...')
        self.__lock.acquire()
        logging.debug(u'Lcd locked...')

        self.__lcd.stop_event_handling()
        self.__lcd.reset()

        self.__lock.release()

        logging.info(u'Success shutdown!')

class Applet(object):
    """docstring for Applet."""
    def __init__(self, drawer, cooldown=1):
        super(Applet, self).__init__()
        self._drawer = drawer
        self._cooldown = cooldown

    def startup(self):
        """Draw init image on screen"""
        pass

    def get_cd(self):
        """Getter for _cooldown"""
        return self._cooldown

    def ambient_callback(self, color_rgb):
        """Callback for ambient_light"""
        pass

class UrPidor(Applet):
    """docstring for UrPidor."""
    __TIME_OFFSET = datetime.datetime.now()
    __FREEZE_DELTA = datetime.timedelta(0, 0, 0)
    __FREEZE_TIME = None
    __FREEZE_FLAG = False

    def __init__(self, drawer):
        super(UrPidor, self).__init__(drawer, 0.7)
        self.name = "Watch"
        self.__background = Img.open(os.path.dirname(os.path.abspath(__file__)) + "/../background.png")
        self.__background = self.__background.resize((320, 240), Img.CUBIC)
        self.__background_crop = self.__background.crop((0, 90, 320, 175))
        UrPidor.__TIMER = UrPidor.get_time

        self.__watch_alpha = 0.6
        self.__bg_color = [177, 31, 80, self.__watch_alpha]
        #self.__fps = 0
        #self.__second_time = timeit.default_timer()

    def startup(self):
        """Draw init image on screen"""
        drawer = self._drawer
        time = datetime.datetime.now().strftime("%H:%M:%S")

        drawer.draw_image([0, 0], [320, 240], self.__background)
        drawer.draw_rectangle([0, 90], [320, 85], self.__bg_color)
        drawer.draw_textline([32, 90], 72, time)

    @staticmethod
    def __reset_timer(key, state):
        UrPidor.__TIME_OFFSET = datetime.datetime.now()
        UrPidor.__FREEZE_DELTA = datetime.timedelta(0, 0, 0)
        if UrPidor.__FREEZE_FLAG:
            UrPidor.__FREEZE_TIME = datetime.datetime.now()

    def get_keybind(self):
        return { (Key.BACK, True): self.__reset_timer,
                 (Key.MENU, True): self.__switch,
                 (Key.OK, True): self.__pause }

    @staticmethod
    def get_time(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def __pause(key, state):
        if UrPidor.__FREEZE_FLAG:
            UrPidor.__FREEZE_DELTA += datetime.datetime.now() - UrPidor.__FREEZE_TIME
            UrPidor.__FREEZE_TIME = None
            UrPidor.__FREEZE_FLAG = False
        else:
            UrPidor.__FREEZE_TIME = datetime.datetime.now()
            UrPidor.__FREEZE_FLAG = True

    @staticmethod
    def get_timer(self):
        if UrPidor.__FREEZE_TIME:
            curtime = UrPidor.__FREEZE_TIME
        else:
            curtime = datetime.datetime.now()

        return (datetime.datetime.min + (curtime - UrPidor.__TIME_OFFSET - UrPidor.__FREEZE_DELTA)).time().strftime("%H:%M:%S")

    __TIMER = None

    @staticmethod
    def __switch(key, state):
        if UrPidor.__TIMER == UrPidor.get_time:
            UrPidor.__TIMER = UrPidor.get_timer
        else:
            UrPidor.__TIMER = UrPidor.get_time

    def routine(self):
        """Applet's routine"""
        start_time = timeit.default_timer()
        #fps = 0
        #self.__fps += 1
        #if timeit.default_timer() - self.__second_time > 1.0:
        #    self.__second_time = timeit.default_timer()
        #    fps = self.__fps
        #    self.__fps = 0

        drawer = self._drawer
        time = UrPidor.__TIMER(self)

        drawer.draw_image([0, 90], [320, 85], self.__background_crop)
        drawer.draw_rectangle([0, 90], [320, 85], self.__bg_color)
        drawer.draw_textline([32, 90], 72, time)
        #if fps:
        #    drawer.draw_rectangle([0, 0], [50, 40], [0xff, 0xff, 0xff])
        #    drawer.draw_textline([2, 2], 32, str(fps))


        #print("draw_screen: " + str(timeit.default_timer() - start_time))
        self._cooldown = (0.1 - (timeit.default_timer() - start_time))
        if self._cooldown < 0:
            logging.warn("Cooldown is negative!")
            self._cooldown = 0.2

    def ambient_callback(self, color_rgb):
        """Callback for ambient_light"""
        color_rgba = color_rgb
        color_rgba.append(self.__watch_alpha)
        self.__bg_color = color_rgba


class Notification(Applet):
    """docstring for UrPidor."""
    def __init__(self, drawer, message):
        super(Notification, self).__init__(drawer, 0.7)
        self.name = "Notification"
        self.__background = Img.open(u"/home/grayhook/Изображения/usny.jpg")
        self.__background = self.__background.resize((320, 240), Img.CUBIC)
        self.__watch_alpha = 0.6
        self.__bg_color = [66, 240, 120, self.__watch_alpha]
        self.__message = message
        self._cooldown = 1

    def startup(self):
        """Draw init image on screen"""
        drawer = self._drawer
        time = datetime.datetime.now().strftime("%H:%M:%S")

        drawer.draw_image([0, 0], [320, 240], self.__background)
        drawer.draw_rectangle([0, 0], [320, 240], self.__bg_color)
        drawer.draw_textline([15, 200], 32, time)
        drawer.draw_textline([15, 10], 32, self.__message["summary"])
        try:
            drawer.draw_text_fitted([15, 50], 24, self.__message["body"])
        except Exception as e:
            logging.error(e)


    def routine(self):
        """Applet's routine"""
        pass



def digit_fit_width(digit, width):
    """Fit digit in width and return string"""
    result = str(digit)
    while len(result) < width:
        result = "0" + result
    return result
