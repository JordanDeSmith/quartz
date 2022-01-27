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

MODIFIERS = ['shift','rshift','alt','ctrl','capslock','meta']

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
    def __init__(self, config, config_modifier, layout_file, **kwargs):
        super(EditKeyboard, self).__init__(**kwargs)
        self.config = config
        self.config_modifier = config_modifier
        self.edit_modifiers = set()
        self.lit_button = None
        self.edit_key = None
        self.key_layout = None
        self.layout = BoxLayout(size_hint=(1,1), orientation="vertical")
        self.add_widget(self.layout)
        self.label = Label(size_hint=(1,0.1), text="Select a key to see its config")
        self.layout.add_widget(self.label)
        try:
            self.change_layout(layout_file)
        except ValueError as error:
            print(error) #TODO: Better handle this error

    def change_layout(self, file_name):
        """Changes the edit_keyboard layout"""
        if self.key_layout is not None:
            self.layout.remove_widget(self.key_layout)
        self.key_layout = BoxLayout(orientation='vertical')
        keys = json.load(open(file_name))
        for item in keys:
            self.key_layout.add_widget(self.add_key(item, item["size_hint_y"]))
        self.layout.add_widget(self.key_layout)

    def add_key(self, key, size_hint_y):
        """Separate function to separate scope and keep key_code in each button"""
        if key["type"] == "key":
            return Button(text=key['text'], size_hint_x=key["size_hint_x"], size_hint_y=size_hint_y,
                        on_release=lambda button : self.on_key_up(button, key["key_code"]))
        elif key["type"] == "box_layout":
            boxLayout = BoxLayout(size_hint_y=key["size_hint_y"], size_hint_x=key["size_hint_x"],
                            orientation=key["orientation"])
            for item in key["children"]:
                boxLayout.add_widget(self.add_key(item, size_hint_y))
            return boxLayout
        else:
            raise ValueError("Invalid option in layout file")

    def update_config(self, config):
        #TODO: check if something has been changed and needs to be saved
        self.config = config

    def on_key_up(self, button, key_code):
        """If key in modifiers, highlight it, and add it to local modifiers
            If it's already in local, remove it, and un-highlight it.
            Otherwise update what key we're currently looking at
            Then update a label (which I need to make...) to say what it is set to
            And have something ready that can change what it is set to. 
        """
        if key_code in MODIFIERS:   #FIXME: If having multiple command/alt/etc. breaks if the other is clicked
            if key_code in self.edit_modifiers:
                button.background_color = [1,1,1,1]
                self.edit_modifiers.remove(key_code)
            else:
                self.edit_modifiers.add(key_code)
                button.background_color = 'red'
        else:
            self.edit_key = key_code
            if self.lit_button is not None:
                self.lit_button.background_color = [1,1,1,1]
            button.background_color = 'blue'
            self.lit_button = button
        not_in_config = True
        if self.edit_key in self.config:
            for i in self.config[self.edit_key]:
                if set(i["modifiers"]) == self.edit_modifiers:
                    self.label.text = f'Type: {i["type"]}'
                    if i["type"] == "sound":
                        self.label.text +=  f' Filepath: {i["data"]["filePath"]}'
                    not_in_config = False
                    break;
        if not_in_config:
            self.label.text = "No config"
        

class KeyboardApp(App):
    """Application start for Kivy"""

    CONFIG_PATH = 'configs/'
    LAYOUT_PATH = 'layouts/'

    def build_config(self, config):
        config.setdefaults('keyboard', {
            'last_used_config': None,
            'layout_config':'macbook.json'
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
        json_data += """]
            },
            { "type":"options",
            "title":"layout",
            "desc":"The loaded layout",
            "key": "layout_config",
            "section": "keyboard",
            "options": ["""
        for counter, file in enumerate(self.layout_files):
            json_data += f'"{file}"'
            if counter < len(self.layout_files) - 1:
                json_data += ','
        json_data += "]}]"

        settings.add_json_panel('Keyboard Config', self.config, data=json_data)

    def on_config_change(self, config, section, key, value):
        if config is self.config:
            token = (section,key)
            if token == ('keyboard', 'last_used_config'):
                self.update_config_data(value)
                self.config_button.text = value
            if token == ('keyboard', 'layout_config'):
                self.edit_keyboard.change_layout(self.LAYOUT_PATH + value)



    def update_config_data(self, file_name):
        json_data = json.load(open(self.CONFIG_PATH + file_name))
        self.config_data = {}
        for i in json_data:
            if i["key"] in self.config_data:
                self.config_data[i["key"]].append(
                    {"modifiers":i["modifiers"],"type":i["type"],"data":i["data"]})
            else:
                self.config_data[i["key"]] = [
                    {"modifiers":i["modifiers"],"type":i["type"],"data":i["data"]}]
        for observer in Observer.OBSERVERS:
            if "config_update" in observer.observing:
                observer.observing["config_update"](self.config_data)

    def build(self):
        parent = BoxLayout(orientation='vertical')
        Window.bind(on_request_close=self.on_request_close)
        Window.size = (750,500)
        self.settings = self.config

        self.json_files = []
        for file in os.listdir(os.path.join(os.path.curdir, self.CONFIG_PATH)):
            if file.endswith(".json") and not file.endswith("settings.json"):
                self.json_files.append(file)
        if len(self.json_files) == 0:
            raise RuntimeError("No config files") #TODO: Properly handle there being no config files.

        config_file = ""
        if self.settings.get('keyboard', 'last_used_config') != "None" and self.settings.get(
                'keyboard', 'last_used_config') in self.json_files:
            config_file = self.settings.get('keyboard', 'last_used_config')
        else:
            self.config.set('keyboard', 'last_used_config', self.json_files[0])
            self.config.write()
            config_file = self.json_files[0]
        self.update_config_data(config_file)

        self.layout_files = []
        for file in os.listdir(os.path.join(os.path.curdir, self.LAYOUT_PATH)):
            if file.endswith(".json") and not file.endswith("settings.json"):
                self.layout_files.append(file)
        if len(self.layout_files) == 0:
            raise RuntimeError("No layout files") #TODO: Properly handle no layout files

        layout_file = self.LAYOUT_PATH
        if self.settings.get('keyboard', 'layout_config') != "None" and self.settings.get(
            'keyboard', 'layout_config') in self.layout_files:
            layout_file += self.settings.get('keyboard', 'layout_config')
        else:
            self.config.set('keyboard', 'layout_config', self.layout_files[0])
            self.config.write()
            layout_file += self.layout_files[0]

        #TODO: Move button, label that it opens settings,
        # and make separate label that shows what config we're using.
        self.config_button = Button(text = self.settings.get('keyboard', 'last_used_config'),
            width=200, size_hint=(None,None))
        self.config_button.bind(on_release=self.open_settings)
        parent.add_widget(self.config_button)
        self.keyboard = Keyboard(self.settings, self.config_data)
        self.keyboard.observe("config_update", self.keyboard.update_config)
        parent.add_widget(self.keyboard)
        self.edit_keyboard = EditKeyboard(self.config_data, self.edit_config, layout_file, size_hint=(1,1.2),
            anchor_x='center', anchor_y='center')
        self.edit_keyboard.observe("config_update", self.edit_keyboard.update_config)
        parent.add_widget(self.edit_keyboard)

        return parent

    def on_request_close(self, *args):
        pass #TODO: write out anything we need/check if things have changed

    def edit_config(self, key, modifiers, new_file):
        print(f"Editing config\nKey: {key}\nModifiers: {modifiers}")
        for observer in Observer.OBSERVERS:
            if "config_update" in observer.observing:
                observer.observing["config_update"](self.config_data)

    def reset_settings(self):
        """Resets all settings to default values"""
        self.settings = {"last_used_config": None, "layout_config": None}
        with open("settings.json", 'w') as settings_file:
            json.dump(self.settings, settings_file)
        for observer in Observer.OBSERVERS:
            if "setting_update" in observer.observing:
                observer.observing["setting_update"](self.settings)


if __name__ == '__main__':
    KeyboardApp().run()
