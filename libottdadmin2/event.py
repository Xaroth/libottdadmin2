from .util import LoggableObject

class Event(LoggableObject):
    def __init__(self, origin = None):
        self._handlers = []
        self._origin = origin

    def __iadd__(self, handler):
        self.log.debug("Appending handler: '%r'", handler)
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.log.debug("Removing handler: '%r'", handler)
        self._handlers.remove(handler)
        return self

    def __call__(self, *args, **kwargs):
        origin = kwargs.get('origin', self._origin)
        for handler in self._handlers:
            self.log.debug("Calling handler: '%r'", handler)
            try:
                handler(origin=origin, *args, **kwargs) 
            except TypeError as e:
                handler(*args, **kwargs)

    def clear(self, from_object = None):
        if from_object is None:
            self.log.debug("Removing all handlers")
            self._handlers = []
        else:
            self.log.debug("Removing all handlers from object '%r'", from_object)
            for handler in self._handlers[:]: 
                # Create a copy, since we'll be editing the base list.
                if handler.im_self == from_object:
                    self -= handler
