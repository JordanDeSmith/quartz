import os
import json
from observer import Observer
from sound_keyboard import MODIFIERS
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox

ACTION_TYPES = ['sound', 'stopAll', 'stopLooping']

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
        self.config_modifier = config_modifier
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
        self.looping_label = Label(text="Looping:", size_hint_x=0.5)
        self.editing_box.add_widget(self.looping_label)
        self.loop_check = CheckBox(color=[1,1,1,1], size_hint_x=0.2)
        self.editing_box.add_widget(self.loop_check)
        self.editing_box.add_widget(Button(text="Clear", size_hint=(0.42,1),
            on_release=lambda btn: self.clear()))
        self.editing_box.add_widget(Button(text="Cancel", size_hint=(0.42,1),
            on_release=lambda btn: self.edit(False)))
        self.editing_box.add_widget(Button(size_hint=(0.32,1), text="Save",
            on_release=lambda btn: self.save_change()))


        self.layout = BoxLayout(size_hint=(1,1), orientation="vertical")
        self.add_widget(self.layout)
        
        display_layout = BoxLayout(size_hint=(1,0.1), orientation="horizontal")
        self.layout.add_widget(display_layout)
        self.label = Label(size_hint=(0.4,1), text="Select a key to see its config")

        self.edit_layout = BoxLayout(size_hint=(1,1), orientation="horizontal")
        display_layout.add_widget(self.label)
        display_layout.add_widget(self.edit_layout)
        self.edit(False)
        try:
            self.change_layout(layout_file)
        except ValueError as error:
            print(error) #TODO: Better handle this error

    def save_change(self):
        self.edit(False)
        if (self.new_file is not None or self.edit_type != "sound") and self.edit_key is not None:
            self.config_modifier(self.edit_key, self.edit_modifiers, self.edit_type,
                self.new_file, loopable=self.loop_check._get_active())

    def clear(self):
        self.edit(False)
        self.config_modifier(self.edit_key, self.edit_modifiers, "clear")

    def change_file(self, path, file):
        #TODO: Display the loaded file
        if len(file) > 0:
            self.new_file = os.path.join(path, file[0])
            self.label.text = self.new_file.split('/')[-1]
        else:
            self.new_file = None

    def change_action(self, button, action):
        setattr(button, 'text', action)
        self.edit_type = action
        if action == "sound":
            self.load_file.disabled = False
            self.loop_check.disabled = False
            self.looping_label.disabled = False
        else:
            self.load_file.disabled = True
            self.loop_check.disabled = True
            self.looping_label.disabled = True

    def edit(self, open):
        self.edit_layout.clear_widgets()
        if open:
            self.edit_layout.size_hint=(1,1)
            self.edit_layout.add_widget(self.editing_box)
            start_action = ACTION_TYPES[0]
            if self.edit_key in self.config:
                for i in self.config[self.edit_key]:
                    if set(i["modifiers"]) == self.edit_modifiers:
                        start_action = i["type"]
                        if start_action == "sound":
                            self.loop_check._set_active(i["data"]["loopable"])
            else:
                self.loop_check._set_active(False)
            self.drop_down.select(start_action)
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
                    if i["type"] == "sound":
                        self.new_file = i["data"]["filePath"]
                        self.label.text =  i["data"]["filePath"].split("/")[-1]
                        if i["data"]["loopable"]:
                            self.label.text += "    (looping)"
                    else:
                        self.label.text = i["type"]
                    not_in_config = False
                    break;
        if not_in_config:
            self.label.text = "No config"