# runtime.py
# coro-scratch runtime support

import asyncio

greenflags = []
sprites = []

def create_sprite(cls):
    assert issubclass(cls, Sprite), "{} is not a Sprite".format(cls)
    sprite = cls()
    sprites.append(sprite)
    greenflags.extend(sprite._greenflags)

class Sprite:
    def __init__(self):
        scripts = [(script, getattr(self, script)) for script in dir(self) if callable(getattr(self, script))]
        self._greenflags = [script for name, script in scripts if name.startswith("greenflag")]

    @asyncio.coroutine
    def sayfor(self, thing, time):
        "Says thing for time seconds"
        print("{} says {}".format(self.__class__.__name__, thing))
        yield from asyncio.sleep(time)
    @asyncio.coroutine
    def wait(self, time):
        "Waits for times seconds"
        yield from asyncio.sleep(time)
