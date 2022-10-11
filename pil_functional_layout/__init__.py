from .widgets import *
def Keyword(kwa):
    def f(**kwargs):
        nonlocal kwa
        return kwargs[kwa]
    return f