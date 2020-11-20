#!/usr/bin/python3
# coding: utf-8
"""Userspace driver"""

import time
import signal
import dbus
import threading
import logging
from gi.repository import GLib
from g19d.appmgr import AppMgr

CONTEXT = {
    "APPMGR": None,
    "exit": threading.Event()
}


def shutdown(*args):
    """SIGTERM/SIGHUP callback"""
    del args
    CONTEXT["exit"].set()
    print("SIG shutdown")



def routine():
    CONTEXT["APPMGR"] = AppMgr()
    time.sleep(1)
    CONTEXT["APPMGR"].run()


def main():
    """Main"""
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGHUP, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    thread = threading.Thread(target=routine, name='AppMgr thread')
    thread.start()

    CONTEXT["exit"].wait()

    CONTEXT["APPMGR"].shutdown()
    thread.join()


if __name__ == '__main__':
    main()
