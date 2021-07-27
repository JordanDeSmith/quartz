import kivy
from kivy.uix.widget import Widget
kivy.require('2.0.0') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.label import Label
from kivy.core.window import Window

class Keyboard(Widget):
    def __init__(self, **kwargs):
        super(Keyboard, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print("pressed ", text)
        print("modifiers:")
        print(modifiers)


class KeyboardApp(App):

    def build(self):
        keyboard = Keyboard()
        return keyboard


if __name__ == '__main__':
    KeyboardApp().run()