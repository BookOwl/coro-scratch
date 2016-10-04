runtime_greenflags = []
runtime_sprites = []

def create_sprite(cls):
    sprite = cls()
    runtime_sprites.append(sprite)
    runtime_greenflags.extend(sprite._greenflags)

class runtime_Stage:
    def __init__(self):
        scripts = [(script, getattr(self, script)) for script in dir(self) if callable(getattr(self, script))]
        self._greenflags = [script for name, script in scripts if name.startswith("greenflag")]
        self._answer = ""
        self._vars = dict(self.my_vars)
        self._lists = dict(self.my_lists)

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
    def set_var(self, var, value):
        "Sets var to value"
        if var in global_vars:
            global_vars[var] = value
        else:
            self._vars[var] = value
    def change_var(self, var, value):
        "Sets var to value"
        if var in global_vars:
            global_vars[var] = convert_and_run_math("+", global_vars[var], value)
        else:
            self._vars[var] = convert_and_run_math("+", self._vars[var], value)
    def get_var(self, var):
        "Return the value of var"
        if var in global_vars:
            return global_vars[var]
        elif var in self._vars:
            return self._vars[var]
        return 0
    def _get_list(self, listName):
        "Returns the list listName"
        if listName in global_lists:
            return global_lists[listName]
        elif listName in self._lists:
            return self._lists[listName]
        else:
            self._lists[listName] = []
            return self._lists[listName]
    def get_list_as_string(self, listName):
        l = self._get_list(listName)
        if all([len(item) <= 1 for item in l]):
            return "".join(map(str, l))
        else:
            return " ".join(map(str, l))
    def add_to_list(self, thing, listName):
        self._get_list(listName).append(str(thing))
    def insert_thing_in_list(self, thing, place, listName):
        l = self._get_list(listName)
        if place == "last":
            l.append(thing)
        elif place == "random":
            l.insert(random.randrange(0, len(l)), thing)
        else:
            l.insert(int(convert_to_num(place)[0])-1, thing)
    def replace_thing_in_list(self, place, listName, thing):
        l = self._get_list(listName)
        if place == "last":
            l[-1] = thing
        elif place == "random":
            l[random.randrange(0, len(l))] = thing
        else:
            l[int(convert_to_num(place)[0])-1] = thing
    def delete_stuff_from_list(self, amount, listName):
        l = self._get_list(listName)
        if amount == "all":
            l.clear()
        elif amount == "last":
            del l[-1]
        else:
            del l[int(convert_to_num(amount)[0])-1]
    def length_of_list(self, listName):
        return len(self._get_list(listName))
    def list_contains_thing(self, listName, thing):
        return str(thing).lower() in [str(item).lower()
                                      for item in self._get_list(listName)]
    def item_of_list(self, place, listName):
        l = self._get_list(listName)
        if place == "last":
            return l[-1]
        elif place == "random":
            return random.choice(l)
        else:
            return l[int(convert_to_num(place)[0])-1]

def convert_to_num(n):
    "Converts a number string to a Python number"
    if isinstance(n, (int, float)):
        return (n, True)
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

class runtime_Sprite(runtime_Stage):
    @asyncio.coroutine
    def sayfor(self, thing, time):
        "Says thing for time seconds"
        print("{} says '{}'".format(self.__class__.__name__, thing))
        yield from asyncio.sleep(time)
    @asyncio.coroutine
    def say(self, thing):
        "Says thing"
        print("{} says '{}'".format(self.__class__.__name__, thing))
    @asyncio.coroutine
    def thinkfor(self, thing, time):
        "Thinks thing for time seconds"
        print("{} thinks '{}'".format(self.__class__.__name__, thing))
        yield from asyncio.sleep(time)
    @asyncio.coroutine
    def think(self, thing):
        "Thinks thing"
        print("{} thinks '{}'".format(self.__class__.__name__, thing))

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
def pick_random(a, b):
    a, b = map(convert_to_num, (a, b))
    a, b = a[0], b[0]
    if isinstance(a, float) or isinstance(b, float):
        return random.uniform(a, b)
    else:
        return random.randint(a, b)
