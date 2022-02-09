"""Runs a GUI for sound keyboard"""

import os
import json
import kivy
from edit_keyboard import EditKeyboard
from sound_keyboard import SoundKeyboard
from observer import Observer
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
kivy.require('2.0.0')


class SaveChanges(Widget):
    """Popup for asking to save or discard changes"""
    def __init__(self, save_callback, data, file, **kwargs):
        self.exit = False       #Determines if application will exit on popup close
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
        #TODO: Save as, be able to change what file it's saving to/create new one

        self.save_popup.open()

    def close(self, save):
        """Closes the popup, exits application if self.exit is True"""
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
                    SaveChanges(self.save_changes, self.config_data, self.config_file)
                self.config_file = value
                self.update_config_data(value)
                self.config_label.text = f"Config: {value}"
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

        self.config_button = Button(text="Settings",
            width=150, size_hint=(None,None))
        self.config_button.bind(on_release=self.open_settings)
        parent.add_widget(self.config_button)
        self.config_label = Label(text=f"Config: {self.settings.get('keyboard', 'last_used_config')}",
            width=500, size_hint=(None,None))
        parent.add_widget(self.config_label)
        self.keyboard = SoundKeyboard(self.settings, self.config_data)
        self.keyboard.observe("config_update", self.keyboard.update_config)
        parent.add_widget(self.keyboard)
        self.edit_keyboard = EditKeyboard(self.config_data, self.edit_config, layout_file, size_hint=(1,4),
            anchor_x='center', anchor_y='center')
        self.edit_keyboard.observe("config_update", self.edit_keyboard.update_config)
        parent.add_widget(self.edit_keyboard)

        return parent

    def on_request_close(self, *args):
        if self.changed_config:
            SaveChanges(self.save_changes, self.config_data, self.config_file, exit=True)
            return True
        return False

    def save_changes(self, config, file):
        json_string = "["
        first = True
        for key in config:
            for mod in config[key]:
                if key == "\\":
                    key = "\\\\"
                if not first:
                    json_string += ","
                json_string += "{" + f"""
                        "key":"{key}",
                        "modifiers":["""
                first = True
                for modifier in mod["modifiers"]:
                    if not first:
                        json_string += ","
                    else:
                        first= False
                    json_string += f'"{modifier}"'
                json_string += f"""],
                        "type":"{mod["type"]}",
                        "data":""" + "{"
                first = True
                for k, v in mod["data"].items():
                    if not first:
                        json_string += ","
                    else:
                        first = False
                    if isinstance(v, bool):
                        v = str(v).lower()
                    else:
                        v = f'"{v}"'
                    json_string += f'"{k}":{v}'
                json_string += "}"
                json_string += "}"
                first = False
        json_string += "]"

        json_data = json.loads(json_string)
        with open(os.path.join(os.path.curdir, self.CONFIG_PATH, file), 'w', encoding="UTF-8") as out_file:
            out_file.write(json.dumps(json_data, indent=4))
        self.changed_config = False

    def edit_config(self, key, modifiers, new_type, new_file=None, loopable=False):
        #TODO: Currently can save individual sounds, but have to switch config or exit to save entire config
        #TODO: Fix this function, it's super redundant
        modifiers = list(modifiers)
        if key in self.config_data:
            entered = False
            for item in self.config_data.get(key):
                if set(modifiers) == set(item["modifiers"]):
                    entered = True
                    if new_type == "clear":
                        self.config_data.get(key).remove(item)
                    else:
                        item["type"] = new_type
                        if new_type == "sound":
                            item["data"]["filePath"] = new_file
                            item["data"]["loopable"] = loopable
                        else:
                            item["data"] = {}
                    self.changed_config = True #TODO: Only if it's actually changed
            if not entered and new_type != "clear":
                new_data = {"modifiers":modifiers, "type":new_type, "data":{}}
                if new_type == "sound":
                    new_data["data"]["filePath"] = new_file
                    new_data["data"]["loopable"] = loopable
                self.config_data[key].append(new_data)
                self.changed_config = True #TODO: Only if it's actually changed
        elif new_type != "clear":
            new_data = {"modifiers":modifiers, "type":new_type, "data":{}}
            if new_type == "sound":
                    new_data["data"]["filePath"] = new_file
                    new_data["data"]["loopable"] = loopable
            self.config_data[key] = [new_data]
            self.changed_config = True  #TODO: Only if it's actually changed

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
