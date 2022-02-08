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