  Logintech G19 Linux Daemon
============================

  About
-------

  This is userspace driver for Logitech G19.
  
  Features
-------

  + Watch with stopwatch (press "menu" to switch).
  + Full support of [ambient-light](https://github.com/GRayHook/ambient-light). Driver will be like a supervisor: starts `ambient_light` from `PATH`, listening, terminating when it's time. It isn't required, but... C'mon, ambilight. Anyway, if `ambient_light` does not present in `PATH` driver should work fine.
  + Keybindings to python code. Use Pynput to simulate combination of keys.
  + DBus notifying on LCD.

  Requirements
--------------

  + Pyusb
  + Pillow
  + Pynput
