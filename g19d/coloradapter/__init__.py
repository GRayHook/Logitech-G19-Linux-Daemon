# coding: utf-8
"""Adapter for ambient_light"""
import socket
import threading
import struct
import os
import errno
import subprocess
from time import sleep

class ColorAdapter(threading.Thread):
    """docstring for ColorAdapter."""
    def __init__(self, callback):
        super(ColorAdapter, self).__init__()
        self.__evnt = threading.Event()
        self.__callback = callback
        self.__sock = socket.socket()
        self.__last_color = (0, 0, 0)
        self.__ambilight = None
        self.__thread_ambilight = None

    def run(self):
        try:
            self.__sock.bind(('', 51117))
        except OSError as err:
            print("Can't bind socket: ", err)
            return

        self.__sock.listen(1)

        self.__thread_ambilight = threading.Thread(target=self.__ambilight_target,
                                                   name='Ambilight thread')
        self.__thread_ambilight.start()

        while not self.__evnt.is_set():
            self.__conn = self.__sock.accept()[0]
            while not self.__evnt.is_set():
                try:
                    payload = self.__conn.recv(3)
                except OSError as err:
                    if err.errno == errno.EBADF:
                        break
                    raise err

                if payload == None:
                    break

                self.apply_color_from_payload(payload)

    def shutdown(self):
        """Shutdown adapter"""
        self.__evnt.set()
        self.__sock.close()
        if self.__thread_ambilight:
            self.__ambilight.terminate()
            self.__thread_ambilight.join()

    def apply_color_from_payload(self, payload):
        """Apply backlight color to keyboard via callback"""
        try:
            red, green, blue = struct.unpack("!BBB", payload)
        except struct.error as err:
            return
        red, green, blue = red, green, blue
        if (red, green, blue) != self.__last_color:
            self.__last_color = (red, green, blue)
            self.__callback([red, green, blue])

    def __ambilight_target(self):
        def preexec():
            os.setpgrp()

        while not self.__evnt.is_set():
            executable = None
            for path in os.environ["PATH"].split(os.pathsep):
                fname = os.path.join(path, "ambient_light")
                if os.path.isfile(fname) and os.access(fname, os.X_OK):
                    executable = fname
                    break

            fstdout = open("/tmp/ambient.log", "w")
            self.__ambilight = subprocess.Popen(executable, stdout=fstdout,
                                                stderr=fstdout, preexec_fn=preexec)
            self.__ambilight.wait()
            self.__conn.close()
            fstdout.close()

