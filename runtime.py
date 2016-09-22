runtime_greenflags = []
runtime_sprites = []

def create_sprite(cls):
    sprite = cls()
    runtime_sprites.append(sprite)
    runtime_greenflags.extend(sprite._greenflags)

class runtime_Sprite:
    def __init__(self):
        scripts = [(script, getattr(self, script)) for script in dir(self) if callable(getattr(self, script))]
        self._greenflags = [script for name, script in scripts if name.startswith("greenflag")]
        self._answer = ""

    @asyncio.coroutine
    def sayfor(self, thing, time):
        "Says thing for time seconds"
        print("{} says '{}'".format(self.__class__.__name__, thing))
        yield from asyncio.sleep(time)

    @asyncio.coroutine
    def wait(self, time):
        "Waits for times seconds"
        yield from asyncio.sleep(time)

    @asyncio.coroutine
    def ask(self, question):
        "Asks question"
        print("{} asks '{}'".format(self.__class__.__name__, question))
        self._answer = input()

    def answer(self):
        "Returns the answer"
        return self._answer

def convert_to_num(n):
    "Converts a number string to a Python number"
    try:
        return int(n), True
    except ValueError:
        try:
            return int(n, base=16), True
        except ValueError:
            try:
                return float(n), True
            except ValueError:
                return 0, False

def convert_and_run_math(op, a, b):
    num_a, _ = convert_to_num(a)
    num_b, _ = convert_to_num(b)
    return eval("{} {} {}".format(num_a, op, num_b))

def convert_and_run_comp(op, a, b):
    if op == "=":
        op = "=="
    num_a, a_is_num = convert_to_num(a)
    num_b, b_is_num = convert_to_num(b)
    if not a_is_num or not b_is_num:
        return eval("{} {} {}".format(repr(str(a)), op, repr(str(b))))
    else:
        return eval("{} {} {}".format(num_a, op, num_b))
