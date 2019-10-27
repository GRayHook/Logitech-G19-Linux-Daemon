# coding: utf-8
"""Adapter for ambient_light"""
import socket
import threading
import struct

class ColorAdapter(threading.Thread):
    """docstring for ColorAdapter."""
    def __init__(self, callback):
        super(ColorAdapter, self).__init__()
        self.daemon = True
        self.__evnt = threading.Event()
        self.__callback = callback
        self.__sock = socket.socket()

    def run(self):
        self.__sock.bind(('', 51117))
        self.__sock.listen(1)
        while not self.__evnt.is_set():
            conn = self.__sock.accept()[0]
            while True:
                self.apply_color_from_socket(conn)

    def shutdown(self):
        """Shutdown adapter"""
        self.__evnt.set()
        self.__sock.close()

    def apply_color_from_socket(self, sock):
        """Apply backlight color to keyboard via callback"""
        red, green, blue = struct.unpack("iii", sock.recv(12))
        red, green, blue = red * 255 / 63, green * 255 / 63, blue * 255 / 63
        print "r(%d) g(%d) b(%d)" % (red, green, blue)
        self.__callback([red, green, blue])
