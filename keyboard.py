"""Runs a GUI for sound keyboard"""

from wave import Error as Wave_Error
import os
import json
import kivy
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window
from soundPlayer import SoundPlayer
kivy.require('2.0.0')

MODIFIERS = ['shift','rshift','alt','ctrl','capslock','meta']
ACTION_TYPES = ['sound', 'stopAll', 'stopLooping']

class Observer():
    """Allows for observers to listen to different events
        For the callback to be used, the observable needs
        to make a call to notify with the event name and data
    """
    OBSERVERS = []
    def __init__(self):
        Observer.OBSERVERS.append(self)
        self.observing = {}
    def observe(self, event, callback):
        self.observing[event] = callback
    def notify(event, data):
        for observer in Observer.OBSERVERS:
            if event in observer.observing:
                observer.observing[event](data)

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

class LoadFile(BoxLayout):
    """Loads a sound file"""
    def __init__(self, load_callback, **kwargs):
        super(LoadFile, self).__init__(**kwargs)
        self.load_callback = load_callback
        self.file_chooser = FileChooserListView(filters=['*.wav'], path='./sounds/')
        self.popup_layout = BoxLayout(orientation="vertical")
        self.popup_layout.add_widget(self.file_chooser)
        self._popup = Popup(title="Load file", content=self.popup_layout,
                size_hint=(0.9, 0.9))
        self.popup_layout.add_widget(Button(size_hint=(1,0.1), text="Cancel", on_release=self._popup.dismiss))
        self.popup_layout.add_widget(Button(size_hint=(1,0.1), text="Load", 
            on_release=lambda btn: self.load()))

        self.add_widget(Button(text="Load file", size_hint=(1,1), 
            on_release=lambda button: self._popup.open()))
    
    def load(self):
        self._popup.dismiss()
        self.load_callback(self.file_chooser.path, self.file_chooser.selection)

class EditKeyboard(AnchorLayout, Observer):
    """Displays keyboard and allows for edits to config"""
    def __init__(self, config, config_modifier, layout_file, **kwargs):
        super(EditKeyboard, self).__init__(**kwargs)
        self.config = config
        self.new_file = None
        self.edit_modifiers = set()
        self.edit_key = None
        self.edit_type = None
        self.lit_button = None
        self.key_layout = None
        self.edit_button = Button(size_hint=(1,1), text="Edit", 
            on_release=lambda button: self.edit(True))
        self.editing_box = BoxLayout(orientation="horizontal")
        self.load_file = LoadFile(self.change_file)
        self.drop_down = DropDown()
        for action in ACTION_TYPES:
            self.drop_down.add_widget(Button(height=50, size_hint_y=None, text=action, 
                on_release=lambda btn: self.drop_down.select(btn.text)))
        type_button = Button(size_hint=(0.6,1), text=ACTION_TYPES[0], on_release=self.drop_down.open)
        self.drop_down.bind(on_select=lambda instance, x: self.change_action(type_button, x))
        self.editing_box.add_widget(type_button)
        self.editing_box.add_widget(self.load_file)
        self.editing_box.add_widget(Button(text="Cancel", size_hint=(0.3,1),
            on_release=lambda btn: self.edit(False)))
        self.editing_box.add_widget(Button(size_hint=(0.3,1), text="Save",
            on_release=lambda btn: self.save_change(config_modifier)))


        self.layout = BoxLayout(size_hint=(1,1), orientation="vertical")
        self.add_widget(self.layout)
        
        display_layout = BoxLayout(size_hint=(1,0.1), orientation="horizontal")
        self.layout.add_widget(display_layout)
        self.label = Label(size_hint=(1,1), text="Select a key to see its config")

        self.edit_layout = BoxLayout(size_hint=(1,1), orientation="horizontal")
        display_layout.add_widget(self.label)
        display_layout.add_widget(self.edit_layout)
        self.edit(False)
        try:
            self.change_layout(layout_file)
        except ValueError as error:
            print(error) #TODO: Better handle this error

    def save_change(self, config_modifier):
        self.edit(False)
        #TODO: Double check values
        config_modifier(self.edit_key, self.edit_modifiers, self.edit_type,
            self.new_file, loopable=False) #TODO: Get input on whether sound should loop or not

    def change_file(self, path, file):
        #TODO: Display the loaded file
        if len(file) > 0:
            self.new_file = os.path.join(path, file[0])
        else:
            self.new_file = None

    def change_action(self, button, action):
        setattr(button, 'text', action)
        self.edit_type = action
        if action == "sound":
            self.load_file.disabled = False
        else:
            self.load_file.disabled = True

    def edit(self, open):
        self.edit_layout.clear_widgets()
        if open:
            self.edit_layout.size_hint=(1,1)
            self.edit_layout.add_widget(self.editing_box)
            self.drop_down.select(ACTION_TYPES[0])    #TODO: load what the current key type is if valid
        else:
            self.edit_layout.size_hint=(0.1,1)
            self.edit_layout.add_widget(self.edit_button)


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
        self.config = config
        #TODO: Find a better way to make sure this updates
        if self.lit_button is not None:
            self.lit_button.background_color = [1,1,1,1]
            self.lit_button = None
        self.label.text = "Select a key to see its config"

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

class SaveChanges(Widget):
    def __init__(self, save_callback, data, file, **kwargs):
        self.exit = False
        if "exit" in kwargs:
            self.exit = kwargs.get("exit")
            kwargs.pop("exit")            #Kivy's Widget doesn't like any kwargs it's not expecting
        super(SaveChanges, self).__init__(**kwargs)
        self.callback = save_callback
        self.data = data
        self.file = file
        popup_layout = BoxLayout()
        self.save_popup = Popup(title="Unsaved Changes", content=popup_layout, size_hint=(1,0.2))
        popup_layout.add_widget(Label(text="You have unsaved changes"))
        popup_layout.add_widget(Button(text="Discard", 
            on_release=lambda btn: self.close(False)))
        popup_layout.add_widget(Button(text="Save",
            on_release=lambda btn: self.close(True)))

        self.save_popup.open()

    def close(self, save):
        self.save_popup.dismiss()
        if save:
            self.callback(self.data, self.file)
        if self.exit:
            App.get_running_app().stop()


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
                if self.changed_config:
                    SaveChanges(self.save_changes, self.config_data, self.config_file) #FIXME: Pulls filename
                self.config_file = value
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
        Observer.notify("config_update", self.config_data)
        self.changed_config = False

    def build(self):
        parent = BoxLayout(orientation='vertical')
        Window.bind(on_request_close=self.on_request_close)
        Window.size = (750,500)
        self.settings = self.config
        self.changed_config = False
        self.config_file = ""

        self.json_files = []
        for file in os.listdir(os.path.join(os.path.curdir, self.CONFIG_PATH)):
            if file.endswith(".json") and not file.endswith("settings.json"):
                self.json_files.append(file)
        if len(self.json_files) == 0:
            raise RuntimeError("No config files") #TODO: Properly handle there being no config files.

        if self.settings.get('keyboard', 'last_used_config') != "None" and self.settings.get(
                'keyboard', 'last_used_config') in self.json_files:
            self.config_file = self.settings.get('keyboard', 'last_used_config')
        else:
            self.config.set('keyboard', 'last_used_config', self.json_files[0])
            self.config.write()
            self.config_file = self.json_files[0]
        self.update_config_data(self.config_file)

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
        if self.changed_config:
            SaveChanges(self.save_changes, self.config_data, self.config_file, exit=True)
            return True
        else:
            return False

    def save_changes(self, config, file):
        print(f"Saving changes to: {file}")
        self.changed_config = False

    def edit_config(self, key, modifiers, new_type, new_file=None, loopable=False):
        #TODO: Fix this function, it's super redundant
        modifiers = list(modifiers)
        if key in self.config_data:
            entered = False
            for item in self.config_data.get(key):
                if set(modifiers) == set(item["modifiers"]):
                    entered = True
                    item["type"] = new_type
                    if new_type == "sound":
                        item["data"]["filePath"] = new_file
                        item["data"]["loopable"] = loopable
                    else:
                        item["data"] = {}
            if not entered:
                new_data = {"modifiers":modifiers, "type":new_type, "data":{}}
                if new_type == "sound":
                    new_data["data"]["filePath"] = new_file
                    new_data["data"]["loopable"] = loopable
                self.config_data[key].append(new_data)
                self.changed_config = True
        else:
            new_data = {"modifiers":modifiers, "type":new_type, "data":{}}
            if new_type == "sound":
                    new_data["data"]["filePath"] = new_file
                    new_data["data"]["loopable"] = loopable
            self.config_data[key] = [new_data]
            self.changed_config = True

        if self.changed_config:
            Observer.notify("config_update", self.config_data)

    def reset_settings(self):
        """Resets all settings to default values"""
        self.settings = {"last_used_config": None, "layout_config": None}
        with open("settings.json", 'w') as settings_file:
            json.dump(self.settings, settings_file)
        Observer.notify("setting_update", self.settings)


if __name__ == '__main__':
    KeyboardApp().run()
