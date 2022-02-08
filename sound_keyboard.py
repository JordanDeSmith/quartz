from wave import Error as Wave_Error
from soundPlayer import SoundPlayer
from observer import Observer
from kivy.uix.widget import Widget
from kivy.core.window import Window

MODIFIERS = ['shift','rshift','alt','ctrl','capslock','meta']

class SoundKeyboard(Widget, Observer):
    """Main sound keyboard class"""
    sound_player = SoundPlayer()

    def __init__(self, settings, config_data, **kwargs):
        super(SoundKeyboard, self).__init__(**kwargs)
        self.settings = settings
        self.config_data = config_data
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        Window.bind(on_request_close=self.on_request_close)
        self.currently_looping = []

    def update_config(self, config_data):
        self.config_data = config_data

    def on_request_close(self, *args):
        self.stop_all()
        return False

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def stop_all(self):
        """Stops all sounds immediately"""
        self.sound_player.stopAll()

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] not in MODIFIERS and keycode[1] in self.config_data:
            try:
                """ To make capslock not make a difference
                if "capslock" in modifiers:
                    modifiers.remove("capslock")
                """
                modifiers = set(modifiers)
                for i in self.config_data[keycode[1]]:
                    if set(i["modifiers"]) == modifiers:
                        if i["type"] == "sound":
                            if i["data"]["loopable"]:
                                if (keycode[1], modifiers) in self.currently_looping:
                                    self.sound_player.stopRepeating(i["data"]["filePath"])
                                    self.currently_looping.remove((keycode[1], modifiers))
                                else:
                                    self.sound_player.playSound(i["data"]["filePath"], True)
                                    self.currently_looping.append((keycode[1], modifiers))
                            else:
                                self.sound_player.playSound(i["data"]["filePath"])
                        elif i["type"] == "stopAll":
                            self.sound_player.stopAll()
                            self.currently_looping = []
                        elif i["type"] == "stopLooping":
                            self.sound_player.stopAllRepeating()
                            self. currently_looping = []
                        break
            except FileNotFoundError as error:
                print(error)
            except Wave_Error as wave_error:
                print(wave_error)
            except ValueError as error:
                print(error)

        return True