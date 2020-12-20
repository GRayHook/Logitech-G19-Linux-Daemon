import datetime
import timeit
import os
from gi.repository import GLib
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import threading
import logging

from g19d.apps import Applet
import PIL.Image as Img
import g19d.libdraw as libdraw
from g19d.logitech.g19_keys import Key

class Notification(Applet):
    LISTED = 0
    """docstring for UrPidor."""
    def __init__(self, appmgr):
        super(Notification, self).__init__(appmgr)
        self.name = "Notification"
        DBusGMainLoop(set_as_default=True)
        self.__background = Img.open(os.path.dirname(os.path.abspath(__file__)) + "/../background.png")
        self.__background = self.__background.resize((320, 240), Img.CUBIC)
        self.__watch_alpha = 0.6
        self.__bg_color = [66, 240, 120, self.__watch_alpha]
        self._cooldown = 1
        self.__notification_loop = GLib.MainLoop()
        self.__notification_thread = threading.Thread(target=self._loop, name='Notification thread')
        self.__notification_thread.start()

    def __draw_message(self, message):
        """Draw init image on screen"""
        drawer = self._drawer
        time = datetime.datetime.now().strftime("%H:%M")

        drawer.draw_image([0, 0], [320, 240], self.__background)
        drawer.draw_rectangle([0, 0], [320, 240], self.__bg_color)
        drawer.draw_textline([15, 200], 32, time)
        drawer.draw_textline([15, 10], 32, message["summary"])
        try:
            drawer.draw_text_fitted([15, 50], 24, message["body"])
        except Exception as e:
            logging.error(e)

    def _loop(self):
        if self._exit.wait(timeout=10):
            return
        session_bus = dbus.SessionBus()
        session_bus.add_match_string_non_blocking(
            "eavesdrop=true, interface='org.freedesktop.Notifications', member='Notify'")
        session_bus.add_message_filter(self.__print_notification)
        session_bus.call_on_disconnection(self.shutdown)
        self.__notification_loop.run()

    def __print_notification(self, bus, message):
        if self._exit.is_set():
            return
        keys = ["app_name", "replaces_id", "app_icon", "summary",
                "body", "actions", "hints", "expire_timeout"]
        args = message.get_args_list()
        if len(args) == 8:
            notification = dict([(keys[i], args[i]) for i in range(8)])

            self.__draw_message(notification)
            self._save_frame_data()
            self._appmgr.irq(self)
            timeout = notification["expire_timeout"] / 1000 \
                      if 2000 <= notification["expire_timeout"] <= 10000 \
                      else 4
            self._exit.wait(timeout=timeout)
            self._appmgr.unirq()

    def shutdown(self):
        logging.debug(u'Notify loop...')
        self._exit.set()
        if self.__notification_loop.is_running():
            self.__notification_loop.quit()

    def get_keybind(self):
        def close_notification(key, state):
            # Notifications are less depending on _exit flag, let's hack it to interrupt __print_notification
            self._exit.set()
            self._exit.clear()

        return { (Key.BACK, True): close_notification }
