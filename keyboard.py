from soundPlayer import SoundPlayer
import os
import json
import kivy
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.core.window import Window
kivy.require('2.0.0')

class Keyboard(Widget):
    soundPlayer = SoundPlayer()
    BASE_DIRECTORY = "./sounds/"

    def __init__(self, **kwargs):
        super(Keyboard, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.add_widget(Label(text="Keyboard", pos=(100,100)))

        #TODO: Load the last used file first. 
        self.jsonFiles = []
        for file in os.listdir():
            if file.endswith(".json"):
                self.jsonFiles.append(file)
        jsonData = json.load(open(self.jsonFiles[0]))
        self.configData = {}
        for i in jsonData:
            if i["key"] in self.configData:
                self.configData[i["key"]].append({"modifiers":i["modifiers"],"type":i["type"],"data":i["data"]})
            else:
                self.configData[i["key"]] = [{"modifiers":i["modifiers"],"type":i["type"],"data":i["data"]}]
        self.currentlyLooping = []

        dropDown = DropDown()
        for i in self.jsonFiles:
            btn = Button(text=i, size_hint_y=None, height=30, width=200)
            btn.bind(on_release=lambda btn: dropDown.select(btn.text))
            dropDown.add_widget(btn)

        self.configButton = Button(text = self.jsonFiles[0], width=200, size_hint=(None,None), pos=(200,200))
        self.configButton.bind(on_release=dropDown.open)

        dropDown.bind(on_select=lambda instance, x: self.change_config(x))
        self.add_widget(self.configButton)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None
    
    def stopAll(self):
        self.soundPlayer.stopAll()

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        MODIFIERS = ['shift','rshift','alt','alt-gr','lctrl','rctrl']
        if (keycode[1] not in MODIFIERS):
            try:
                if keycode[1] in self.configData:
                    for i in self.configData[keycode[1]]:
                        if (set(i["modifiers"]) == set(modifiers)):
                            if i["type"] == "sound":
                                if (i["data"]["loopable"]):
                                    if ((keycode[1], modifiers) in self.currentlyLooping):
                                        self.soundPlayer.stopRepeating(i["data"]["filePath"])
                                        self.currentlyLooping.remove((keycode[1], modifiers))
                                    else:
                                        self.soundPlayer.playSound(i["data"]["filePath"], True)
                                        self.currentlyLooping.append((keycode[1], modifiers))
                                else:
                                    self.soundPlayer.playSound(i["data"]["filePath"])
                            elif i["type"] == "stopAll":
                                self.soundPlayer.stopAll()
                                self.currentlyLooping = []
                            elif i["type"] == "stopLooping":
                                self.soundPlayer.stopAllRepeating()
                                self. currentlyLooping = []
                            break;
            except FileNotFoundError as e:
                print(e)
            except ValueError as e:
                print(e)

        return True

    def change_config(self, configFile):
        jsonData = json.load(open(configFile))
        self.configData = {}
        for i in jsonData:
            if i["key"] in self.configData:
                self.configData[i["key"]].append({"modifiers":i["modifiers"],"type":i["type"],"data":i["data"]})
            else:
                self.configData[i["key"]] = [{"modifiers":i["modifiers"],"type":i["type"],"data":i["data"]}]
        setattr(self.configButton, "text", configFile)


class KeyboardApp(App):
    def build(self):
        parent = Widget()
        self.keyboard = Keyboard()
        parent.add_widget(self.keyboard)
        exitButton = Button(text="Exit")
        exitButton.bind(on_press=self.exit)
        parent.add_widget(exitButton)
        return parent
    
    def exit(self, event):
        self.keyboard.stopAll()
        self.stop()


if __name__ == '__main__':
    KeyboardApp().run()