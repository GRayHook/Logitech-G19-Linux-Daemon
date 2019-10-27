#!/usr/bin/python
# coding: utf-8
"""Userspace driver"""

import time
import signal
import sys
from appmgr import AppMgr

APPMGR = AppMgr()


def shutdown(*args):
    """SIGTERM/SIGHUP callback"""
    del args
    print "SIG shutdown"
    sys.stdout.flush()
    sys.stderr.flush()
    APPMGR.shutdown()
    exit()

def main():
    """Main"""

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGHUP, shutdown)

    APPMGR.routine()

if __name__ == '__main__':
    main()
