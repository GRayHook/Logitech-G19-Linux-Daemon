# coding: utf-8
"""Key listener for G19 (only G19 just bucause of restrictions of original driver)"""
from pykeyboard import PyKeyboard
from logitech.g19_keys import (Data, Key)

class KeyBindings(object):
    '''Simple color changing.

    Enable M1..3 for red/green/blue and use the scroll to change the intensity
    for the currently selected colors.

    '''

    def __init__(self, lg19):
        self.__lg19 = lg19
        self.__cur_m = Data.LIGHT_KEY_M1
        self.__keyboard = PyKeyboard(':0')
        self.__macros_list = {
            (Key.G01, True): self.__press_key,
            (Key.G01, False): self.__press_key
        }
        self.__key_binds = {
            Key.G01: self.__keyboard.function_keys[1],
            Key.G02: self.__keyboard.function_keys[2],
            Key.G03: self.__keyboard.function_keys[3],
            Key.G04: self.__keyboard.function_keys[4],
            Key.G05: self.__keyboard.function_keys[5],
            Key.G06: self.__keyboard.function_keys[6],
            Key.G07: self.__keyboard.function_keys[7],
            Key.G08: self.__keyboard.function_keys[8],
            Key.G09: self.__keyboard.function_keys[9],
            Key.G10: self.__keyboard.function_keys[10],
            Key.G11: self.__keyboard.function_keys[11],
            Key.G12: self.__keyboard.function_keys[12]
        }

    def _update_leds(self):
        '''Updates M-leds according to enabled state.'''
        self.__lg19.set_enabled_m_keys(self.__cur_m)

    def __press_key(self, key, state):
        keyboard_key = self.__key_binds.get(key, False)
        print "PRESS KEY"
        if not keyboard_key:
            return False

        if state:
            self.__keyboard.press_key(keyboard_key)
        else:
            self.__keyboard.release_key(keyboard_key)

        return True


    def __execute_macros(self, evnt):
        """Execute macros which bind on pressed key"""
        processed = False
        for key in xrange(Key.G01, Key.G12 + 1):
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
        print "KB processed - " + str(processed)

        return processed
