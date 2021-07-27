import kivy
from kivy.uix.widget import Widget
kivy.require('2.0.0') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window

class Keyboard(Widget):

    def __init__(self, **kwargs):
        super(Keyboard, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.add_widget(Label(text="Keyboard", pos=(100,100)))

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        MODIFIERS = ['shift','rshift','alt','alt-gr','lctrl','rctrl']
        if (keycode[1] not in MODIFIERS):
            print("pressed ", keycode)
            print("modifiers:")
            print(modifiers)
        return True


class KeyboardApp(App):
    def build(self):
        parent = Widget()
        parent.add_widget(Keyboard())
        exitButton = Button(text="Exit")
        exitButton.bind(on_press=self.exit)
        parent.add_widget(exitButton)
        return parent
    
    def exit(self, event):
        self.stop()


if __name__ == '__main__':
    KeyboardApp().run()