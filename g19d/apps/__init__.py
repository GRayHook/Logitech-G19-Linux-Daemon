import threading

import g19d.libdraw as libdraw

class Applet(object):
    LISTED = 1

    """docstring for Applet."""
    def __init__(self, appmgr):
        super(Applet, self).__init__()
        self._appmgr = appmgr
        self._drawer = libdraw.Drawer()
        self._exit = threading.Event()

        self._thread = threading.Thread(target=self._loop)

    def run(self):
        self._startup()
        self._save_frame_data()
        self._thread.start()

    def shutdown(self):
        self._exit.set()
        self._thread.join()

    def _startup(self):
        """Draw init image on screen"""
        pass

    def _loop(self):
        while not self._exit.is_set():
            pass

    def get_interval(self):
        """Getter for _cooldown"""
        return 0.1

    def _save_frame_data(self):
        self._frame_data = self._drawer.get_frame_data()

    def get_frame_data(self):
        return self._frame_data

    def ambient_callback(self, color_rgb):
        """Callback for ambient_light"""
        pass


if __name__ == '__main__':
    exit(1)
