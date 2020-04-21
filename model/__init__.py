import functools
from .cls import Error

def magic_func(inputs, outputs, requires_all=True):
    from .clsnodes import Field
    from .cls import MagicFunc
    def decorator(func):
        finputs = list(map(Field, inputs))
        foutputs = list(map(Field, outputs))
        @functools.wraps(func)
        def new_func(*args):
            if requires_all and None in args:
                return tuple(None for output in foutputs)
            try:
                return func(*args)
            except Exception as e:
                return Error(str(e))
        return MagicFunc(func.__name__, finputs, foutputs, new_func)
    return decorator
