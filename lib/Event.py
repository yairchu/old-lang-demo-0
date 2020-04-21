class Event(object):
    def __init__(self):
        self.callbacks = []
    def register(self, callback):
        self.callbacks.append(callback)
    def unregister(self, callback):
        self.callbacks.remove(callback)
    def __call__(self, *args, **kw):
        for callback in self.callbacks:
            try:
                callback()
            except:
                print("Unhandled exception in event handler:", self, callback)
                import traceback
                traceback.print_exc()
