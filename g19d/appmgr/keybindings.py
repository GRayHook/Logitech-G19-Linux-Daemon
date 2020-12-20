# coding: utf-8
"""Key listener for G19 (only G19 just bucause of restrictions of original driver)"""
import pynput.keyboard as keyboard
from g19d.logitech.g19_keys import (Data, Key)

class KeyBindings(object):
    '''Simple color changing.

    Enable M1..3 for red/green/blue and use the scroll to change the intensity
    for the currently selected colors.

    '''

    def __init__(self, lg19):
        self.__lg19 = lg19
        self.__cur_m = Data.LIGHT_KEY_M1
        self.__keyboard = keyboard.Controller()
        self.__macros_list = {
        }
        self.__key_binds = {
            Key.G01: keyboard.Key.f1,
            Key.G02: keyboard.Key.f2,
            Key.G03: keyboard.Key.f3,
            Key.G04: keyboard.Key.f4,
            Key.G05: keyboard.Key.f5,
            Key.G06: keyboard.Key.f6,
            Key.G07: keyboard.Key.f7,
            Key.G08: keyboard.Key.f8,
            Key.G09: keyboard.Key.f9,
            Key.G10: keyboard.Key.f10,
            Key.G11: keyboard.Key.f11,
            Key.G12: keyboard.Key.f12
        }

    def register_keybind(self, key):
        self.__macros_list.update(key)

    def drop_keybind(self):
        self.__macros_list = {}

    def _update_leds(self):
        '''Updates M-leds according to enabled state.'''
        self.__lg19.set_enabled_m_keys(self.__cur_m)

    def __press_key(self, key, state):
        keyboard_key = self.__key_binds.get(key, False)
        if not keyboard_key:
            return False

        if state:
            self.__keyboard.press(keyboard_key)
        else:
            self.__keyboard.release(keyboard_key)

        return True


    def __execute_macros(self, evnt):
        """Execute macros which bind on pressed key"""
        processed = False
        for key in range(Key.G01, Key.WINKEY_SWITCH):
            if key in evnt.keysDown:
                state = True
                callback = self.__macros_list.get((key, True), self.__press_key)
            elif key in evnt.keysUp:
                state = False
                callback = self.__macros_list.get((key, False), self.__press_key)
            else:
                continue

            if callable(callback):
                processed = callback(key, state)

        return processed


    def get_input_processor(self):
        """Getter"""
        return self

    def process_input(self, evt):
        """Handler for keyboard listener"""
        processed = False
        # TODO: Move M-keys to macros
        if Key.M1 in evt.keysDown:
            self.__cur_m = Data.LIGHT_KEY_M1
            processed = True
        if Key.M2 in evt.keysDown:
            self.__cur_m = Data.LIGHT_KEY_M2
            processed = True
        if Key.M3 in evt.keysDown:
            self.__cur_m = Data.LIGHT_KEY_M3
            processed = True

        self._update_leds()

        processed = processed or self.__execute_macros(evt)

        return processed
