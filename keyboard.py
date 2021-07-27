from soundPlayer import SoundPlayer
import kivy
import os
import json
from kivy.uix.widget import Widget
kivy.require('2.0.0') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window

class Keyboard(Widget):
    soundPlayer = SoundPlayer()
    BASE_DIRECTORY = "./sounds/"

    def getFile(self, soundName):
        """Given the name of the sound file, returns the full file from the 'sounds' directory"""
        path = os.path.join(os.path.curdir, 'sounds/Sounds', soundName + '.wav')
        if os.path.exists(path):
            return path
        else:
            raise FileNotFoundError("No file with name " + soundName)

    def __init__(self, **kwargs):
        super(Keyboard, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.add_widget(Label(text="Keyboard", pos=(100,100)))

        self.configData = json.load(open('config.json'))
        self.currentlyLooping = []

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None
    
    def stopAll(self):
        self.soundPlayer.stopAll()

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        MODIFIERS = ['shift','rshift','alt','alt-gr','lctrl','rctrl']
        if (keycode[1] not in MODIFIERS):
            print("pressed ", keycode)
            print("modifiers:")
            print(modifiers)
        try:
            for i in self.configData:
                if (i["key"] == keycode[1] and i["modifiers"] == modifiers):
                    if i["type"] == "sound":
                        if (i["loopable"]):
                            if ([keycode[1], modifiers] in self.currentlyLooping):
                                print("Stopping looping " + i["filePath"])
                                self.soundPlayer.stopRepeating(i["filePath"])
                                self.currentlyLooping.remove([keycode[1], modifiers])
                            else:
                                print("Starting looping " + i["filePath"])
                                self.soundPlayer.playSound(i["filePath"], True)
                                self.currentlyLooping.append([keycode[1], modifiers])
                        else:
                            print("Playing " + i["filePath"])
                            self.soundPlayer.playSound(i["filePath"])
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