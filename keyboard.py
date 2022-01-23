"""Runs a GUI for sound keyboard"""

from wave import Error as Wave_Error
import os
import json
import kivy
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window
from soundPlayer import SoundPlayer
kivy.require('2.0.0')

MODIFIERS = ['shift','rshift','alt','alt-gr','lctrl','rctrl','capslock']

class Observer():
    OBSERVERS = []
    def __init__(self):
        Observer.OBSERVERS.append(self)
        self.observing = {}
    def observe(self, event, callback):
        self.observing[event] = callback

class Keyboard(Widget, Observer):
    """Main keyboard class"""
    sound_player = SoundPlayer()
    CONFIG_PATH = 'configs/'

    def __init__(self, settings, config_data, **kwargs):
        super(Keyboard, self).__init__(**kwargs)
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

class EditKeyboard(AnchorLayout, Observer):
    """Displays keyboard and allows for edits to config"""
    def __init__(self, config, config_modifier, **kwargs):
        super(EditKeyboard, self).__init__(**kwargs)
        self.config = config
        self.config_modifier = config_modifier
        """self.keyboard = VKeyboard(on_key_up=self.on_key_up)
        self.keyboard.size = (1500,500)
        self.keyboard.bind(on_key_up=self.on_key_up)
        self.add_widget(self.keyboard)"""
        keyLayout = BoxLayout(orientation='vertical')
        keys = [ #TODO: This works as a proof of concept, but really needs to be created better
            ['esc','F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12'],
            ['`','1','2','3','4','5','6','7','8','9','0','-','=','delete'],
            ['tab','q','w','e','r','t','y','u','i','o','p','[',']','\\',],
            ['caps lock','a','s','d','f','g','h','j','k','l',';','\'','enter'],
            ['shift', 'z','x','c','v','b','n','m',',','.','/','shift'],
            ['function','control','command','space bar','command','option','<-','^','\/','->']
        ]
        for row in keys:
            rowLayout = BoxLayout(orientation='horizontal')
            for key in row:
                rowLayout.add_widget(Button(text=key, on_release=self.on_key_up))
            keyLayout.add_widget(rowLayout)
        self.add_widget(keyLayout)

    def update_config(self, config):
        #TODO: check if something has been changed and needs to be saved
        self.config = config

    def on_key_up(self, button):
        print(f"Pressed {button.text}")
        if button.background_color != [0.0, 0.0, 1.0, 1.0]:
            button.background_color = 'blue'
        else:
            button.background_color ='red'

class KeyboardApp(App):
    """Application start for Kivy"""
    def build_config(self, config):
        config.setdefaults('keyboard', {
            'last_used_config': None
        })

    def build_settings(self, settings):
        json_data = """[{ 
            "type": "title",
            "title": "Keyboard" 
            },
            { "type": "options",
            "title": "Config",
            "desc": "The loaded configuration",
            "section": "keyboard",
            "key": "last_used_config",
            "options": ["""
        for counter, file in enumerate(self.json_files):
            json_data += f'"{file}"'
            if counter < len(self.json_files) - 1:
                json_data += ','
        json_data += "]}]"
        
        settings.add_json_panel('Keyboard Config', self.config, data=json_data)

    def on_config_change(self, config, section, key, value):
        if config is self.config:
            token = (section,key)
            if token == ('keyboard', 'last_used_config'):
                self.update_config_data(value)
                self.keyboard.update_config(self.config_data)
                self.edit_keyboard.update_config(self.config_data)
                self.config_button.text = value

    def update_config_data(self, file_name):
        json_data = json.load(open(Keyboard.CONFIG_PATH + file_name))
        self.config_data = {}
        for i in json_data:
            if i["key"] in self.config_data:
                self.config_data[i["key"]].append(
                    {"modifiers":i["modifiers"],"type":i["type"],"data":i["data"]})
            else:
                self.config_data[i["key"]] = [
                    {"modifiers":i["modifiers"],"type":i["type"],"data":i["data"]}]

    def build(self):
        parent = BoxLayout(orientation='vertical')
        Window.bind(on_request_close=self.on_request_close)
        Window.size = (750,500)
        self.settings = self.config

        self.json_files = []
        for file in os.listdir(os.path.join(os.path.curdir, Keyboard.CONFIG_PATH)):
            if file.endswith(".json") and not file.endswith("settings.json"):
                self.json_files.append(file)
        if len(self.json_files) == 0:
            raise RuntimeError("No config files") #TODO: Properly handle there being no config files.

        if self.settings.get('keyboard', 'last_used_config') != "None" and self.settings.get(
                'keyboard', 'last_used_config') in self.json_files:
            self.update_config_data(self.settings.get('keyboard', 'last_used_config'))
        else:
            self.config.set('keyboard', 'last_used_config', self.json_files[0])
            self.config.write()
            self.update_config_data(self.json_files[0])

        #TODO: Move button, label that it opens settings,
        # and make separate label that shows what config we're using.
        self.config_button = Button(text = self.settings.get('keyboard', 'last_used_config'),
            width=200, size_hint=(None,None))
        self.config_button.bind(on_release=self.open_settings)
        parent.add_widget(self.config_button)
        self.keyboard = Keyboard(self.settings, self.config_data)
        self.keyboard.observe("config_update", self.keyboard.update_config)
        parent.add_widget(self.keyboard)
        self.edit_keyboard = EditKeyboard(self.config_data, self.edit_config, size_hint=(1,1.2),
            anchor_x='center', anchor_y='center')
        self.edit_keyboard.observe("config_update", self.edit_keyboard.update_config)
        parent.add_widget(self.edit_keyboard)

        return parent

    def on_request_close(self, *args):
        pass #TODO: write out anything we need/check if things have changed

    def edit_config(self, key, modifiers, new_file):
        print("Editing config")
        for observer in Observer.OBSERVERS:
            if "config_update" in observer.observing:
                observer.observing["config_update"](self.config_data)

    def reset_settings(self):
        """Resets all settings to default values"""
        self.settings = {"last_used_config": None}
        with open("settings.json", 'w') as settings_file:
            json.dump(self.settings, settings_file)
        for observer in Observer.OBSERVERS:
            if "setting_update" in observer.observing:
                observer.observing["setting_update"](self.settings)


if __name__ == '__main__':
    KeyboardApp().run()
