"""Runs a GUI for sound keyboard"""

from wave import Error as Wave_Error
import os
import json
import kivy
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.core.window import Window
from soundPlayer import SoundPlayer
kivy.require('2.0.0')

MODIFIERS = ['shift','rshift','alt','alt-gr','lctrl','rctrl','capslock']

class Keyboard(Widget):
    """Main keyboard class"""
    sound_player = SoundPlayer()
    CONFIG_PATH = 'configs/'

    def __init__(self, **kwargs):
        super(Keyboard, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.add_widget(Label(text="Keyboard", pos=(100,100)))

        self.settings = {}
        if not os.path.exists('settings.json'):
            print("No settings file: creating new")
            open("settings.json", 'w+')
            self.reset_settings()
        with open("settings.json") as settings_file:
            self.settings = json.load(settings_file)

        self.json_files = []
        for file in os.listdir(os.path.join(os.path.curdir, Keyboard.CONFIG_PATH)):
            if file.endswith(".json") and not file.endswith("settings.json"):
                self.json_files.append(file)
        if len(self.json_files) == 0:
            raise RuntimeError("No config files") #TODO: Properly handle there being no config files.

        if self.settings["lastUsedConfig"] is None:
            json_data = json.load(open(Keyboard.CONFIG_PATH + self.json_files[0]))
            self.settings["lastUsedConfig"] = self.json_files[0]
        else:
            json_data = json.load(open(Keyboard.CONFIG_PATH + self.settings["lastUsedConfig"]))
        self.config_data = {}
        for i in json_data:
            if i["key"] in self.config_data:
                self.config_data[i["key"]].append(
                    {"modifiers":i["modifiers"],"type":i["type"],"data":i["data"]})
            else:
                self.config_data[i["key"]] = [
                    {"modifiers":i["modifiers"],"type":i["type"],"data":i["data"]}]
        self.currently_looping = []

        drop_down = DropDown()
        for i in self.json_files:
            btn = Button(text=i, size_hint_y=None, height=30, width=200)
            btn.bind(on_release=lambda btn: drop_down.select(btn.text))
            drop_down.add_widget(btn)

        self.config_button = Button(text = self.settings["lastUsedConfig"],
            width=200, size_hint=(None,None), pos=(200,200))
        self.config_button.bind(on_release=drop_down.open)

        drop_down.bind(on_select=lambda instance, x: self.change_config(x))
        self.add_widget(self.config_button)

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

    def change_config(self, config_file):
        """Changes the loaded config file"""
        json_data = json.load(open(Keyboard.CONFIG_PATH + config_file))
        self.config_data = {}
        for i in json_data:
            if i["key"] in self.config_data:
                self.config_data[i["key"]].append(
                    {"modifiers":i["modifiers"],"type":i["type"],"data":i["data"]})
            else:
                self.config_data[i["key"]] = [
                    {"modifiers":i["modifiers"],"type":i["type"],"data":i["data"]}]
        setattr(self.config_button, "text", config_file)
        self.settings["lastUsedConfig"] = config_file

    def reset_settings(self):
        """Resets all settings to default values"""
        self.settings = {"lastUsedConfig": None}
        with open("settings.json", 'w') as settings_file:
            json.dump(self.settings, settings_file)


class KeyboardApp(App):
    """Application start for Kivy"""
    def build(self):
        parent = Widget()
        self.keyboard = Keyboard()
        parent.add_widget(self.keyboard)
        exit_button = Button(text="Exit")
        exit_button.bind(on_press=self.exit)
        parent.add_widget(exit_button)
        return parent

    def exit(self, event):
        """Stops all sounds and writes out settings before stopping"""
        self.keyboard.stop_all()
        with open("settings.json", 'w') as out_file:
            json.dump(self.keyboard.settings, out_file)
        self.stop()


if __name__ == '__main__':
    KeyboardApp().run()
