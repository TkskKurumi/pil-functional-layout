from .widgets import *
def Keyword(kwa, *args):
    def f(**kwargs):
        nonlocal args
        if(args):
            return kwargs.get(kwa, args[0])
        else:
            return kwargs[kwa]
    return f