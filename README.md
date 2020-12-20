  Logintech G19 Linux Daemon
============================

  About
-------

  This is userspace driver for Logitech G19.
  
  Features
----------

  + Watch with stopwatch (press "menu" to switch, "back" to reset stopwatch, "ok" to pause stopwatch).
  + Full support of [ambient-light](https://github.com/GRayHook/ambient-light). Driver will be like a supervisor: starts `ambient_light` from `PATH`, listening, terminating when it's time. It isn't required, but... C'mon, ambilight. Anyway, if `ambient_light` does not present in `PATH` driver should work fine. Simple configuration available with applet "Backlight control" (press "gear" key to list available applets).
  + Keybindings to python code. Use Pynput to simulate combination of keys.
  + DBus notifying on LCD. (working only for user thar run driver, root will not receive your notification)

  Requirements
--------------

  + Pyusb
  + Pillow
  + Pynput
