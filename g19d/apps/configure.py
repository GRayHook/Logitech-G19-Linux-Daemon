import datetime
import timeit
import os
import logging
from time import sleep
import threading
import PySimpleGUI as sg
import gc

from g19d.apps import Applet
import PIL.Image as Img
import g19d.libdraw as libdraw
from g19d import libcdraw
from g19d.logitech.g19_keys import Key

class Configure(Applet):
    """Control driver config"""
    WAITING = 1
    CONFIGURING = 2
    STATE_NAMES = {
        WAITING: "Press OK to open config window",
        CONFIGURING: "Waiting for the window have closed"
    }
    def __init__(self, appmgr):
        super(Configure, self).__init__(appmgr)
        self.name = "Configure"
        self.__bg_color = [0, 0, 0]
        self.__state = self.WAITING
        self.__changed = threading.Event()
        self.__changed.set()
        self.__thread = None
        self.__window_closed = threading.Event()
        self.__show_window = threading.Event()
        self.__first_try = True

        def open_window():
            while not self._exit.wait(timeout=1):
                if not self.__show_window.is_set():
                    continue
                self.__show_window.clear()

                config = self._load_config()
                watch_config = None
                watch_background = ""
                if "Watch" in config:
                    watch_config = config["Watch"]
                    if "background" in watch_config:
                        watch_background = watch_config["background"]
                watch_background_new = watch_background

                if self.__first_try:
                    self.__first_try = False
                    layout = [
                        [sg.Text("Configure Watch")],
                        [
                            sg.Text("Background(png, jpg): "),
                            sg.In(size=(65, 1), enable_events=True, key="-WATCH BACKGROUND-"),
                            sg.FileBrowse(initial_folder=os.environ.get("HOME", "/"),
                                          file_types=(
                                              ("PNG Files", "*.png"),
                                              ("JPG Files", "*.jpg"),
                                              ("All Files", "*")
                                          )
                            )
                        ],
                        [sg.Button("Save"), sg.Button("Cancel")]
                    ]
                    window = sg.Window("Configure G19d", layout, finalize=True, disable_close=True)
                else:
                    window.un_hide()

                window["-WATCH BACKGROUND-"].update(watch_background)

                while not self._exit.is_set():
                    event, values = window.read(timeout=250)
                    if event == "-WATCH BACKGROUND-":
                        if values["-WATCH BACKGROUND-"]:
                            watch_background_new = values["-WATCH BACKGROUND-"]
                    if event == sg.WIN_CLOSED or event == "Cancel":
                        break
                    if event == "Save":
                        if watch_background == watch_background_new:
                            break
                        if "Watch" not in config:
                            config["Watch"] = {}
                        config["Watch"]["background"] = watch_background_new
                        self._save_config(config)
                        apps = self._appmgr.get_apps_list()
                        for app in apps:
                            app.update_config()
                        break

                window.hide()
                self.__window_closed.set()

        self.__thread = threading.Thread(target=open_window, name='Config window')
        self.__thread.start()

    def _startup(self):
        """Draw init image on screen"""
        drawer = self._drawer
        drawer.draw_rectangle([0, 0], [320, 240], self.__bg_color)
        drawer.draw_rectangle([15, 30], [240, 34], [145, 90, 0])
        drawer.draw_textline([16, 32], 32, "Configure", 0xffff)

    def shutdown(self):
        super(Configure, self).shutdown()
        if self.__thread:
            self.__thread.join()


    def get_keybind(self):
        def open_config_window(key, state):
            if self.__state != self.WAITING:
                return
            self.__state = self.CONFIGURING
            self.__changed.set()
            self.__show_window.set()

        return { (Key.OK, True): open_config_window }

    def _loop(self):
        while not self._exit.is_set():
            start_time = timeit.default_timer()
            if self.__window_closed.is_set():
                self.__window_closed.clear()
                self.__state = self.WAITING
                self.__changed.set()

            if not self.__changed.is_set():
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

        state_name = self.STATE_NAMES[self.__state]
        drawer.draw_textline([31, 81], 18, state_name, 0xffff)
