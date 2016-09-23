# convert.py
# converts a .sb2 into a .py

import zipfile, tokenize, collections
import json as json_

class JSON_Wrap:
    def __new__(cls, data):
        if isinstance(data, dict):
            return super(JSON_Wrap, cls).__new__(cls)
        elif isinstance(data, list):
            return [cls(datum) for datum in data]
        return data
    def __init__(self, data):
        self._data = data
    def __dir__(self):
        return list(self.__data.keys)
    def __repr__(self):
        return repr(self._data)
    def __getattr__(self, attr):
        try:
            return JSON_Wrap(self._data[attr])
        except KeyError:
            raise AttributeError

Sprite = collections.namedtuple("Sprite", "name scripts vars")
Block = collections.namedtuple("Block", "name args")
Variable = collections.namedtuple("Variable", "name val")

def get_json(path):
    "Extracts the json from a .sb2 file"
    with zipfile.ZipFile(path, 'r') as project:
        with project.open("project.json", "r") as data:
            return JSON_Wrap(json_.loads(data.read().decode()))

def get_stage_and_sprites(json):
    "Extracts the sprites from json"
    def convert(script):
        if isinstance(script, list):
            name, *args = script
            converted_args = []
            for arg in args:
                if isinstance(arg, list) and isinstance(arg[0], list):
                    converted_args.append([convert(sub) for sub in arg])
                else:
                    converted_args.append(convert(arg))
            return Block(name, converted_args)
        return script
    sprites = []
    for child in json.children:
        if hasattr(child, "objName"):
            name = child.objName
            scripts = []
            for script in getattr(child, "scripts", []):
                script = script[2]
                if script[0][0] == "procDef":
                    scripts.append([Block("procDef", JSON_Wrap({"name": script[0][1],
                                                                "args": script[0][2],
                                                                "defaults": script[0][3],
                                                                "atomic": script[0][4]})),
                                    *[convert(block) for block in script[1:]]])
                else:
                    scripts.append([convert(block) for block in script])
            vars = [Variable(var.name, var.value) for var in getattr(child, "variables", [])]
            sprites.append(Sprite(name, scripts, vars))
    scripts = []
    for script in getattr(json, "scripts", []):
        script = script[2]
        scripts.append([convert(block) for block in script])
    vars = [Variable(var.name, var.value) for var in getattr(json, "variables", [])]
    return Sprite("Stage", scripts, vars), sprites

def indent(amount, code):
    return "\n".join(" "*amount + line for line in code.split("\n"))

def sprites_to_py(objects, name):
    "Converts the sprites to a .py file"
    header = """#! usr/bin/env python3
# {}

import asyncio

loop = asyncio.get_event_loop()
""".format(name)

    footer = """

def main():
    tasks = [asyncio.ensure_future(script()) for script in runtime_greenflags]
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()

main()"""

    stage, sprites = objects
    global_vars = repr(dict(stage.vars))
    header += "\nglobal_vars = {}\n".format(global_vars)
    header += "\n{}\n".format(open("runtime.py").read())
    converted_stage = convert_object("Stage", stage)
    converted_sprites = [convert_object("Sprite", sprite) for sprite in sprites]
    return header + "{}\n\n".format(converted_stage) + '\n\n'.join(converted_sprites) + footer

def convert_object(type_, sprite):
    "Converts the sprite to a class"
    class_template = """@create_sprite
class {}(runtime_{}):
    my_vars = {}
{}"""
    gf_template = """@asyncio.coroutine
def greenflag{}(self):
{}"""
    custom_template = """@asyncio.coroutine
def {}(self, {}):
{}"""
    funcs = []
    greenflags = 0
    for script in sprite.scripts:
        hat, *blocks = script
        if hat.name == "whenGreenFlag":
            greenflags += 1
            funcs.append(gf_template.format(greenflags, indent(4, convert_blocks(blocks))))
        if hat.name == "procDef":
            block_name = hat.args.name.replace("%", "").replace(" ", "_")
            args = list(zip(hat.args.args, hat.args.defaults))
            args = ", ".join("{}={}".format(name, default) for (name, default) in args)
            body = indent(4, convert_blocks(blocks))
            funcs.append(custom_template.format(block_name, args, body))
    return class_template.format(sprite.name,
                                 type_,
                                 repr([tuple(v) for v in sprite.vars]),
                                 indent(4, ("\n\n".join(funcs) if funcs else "pass")))

def convert_blocks(blocks):
    lines = []
    for block in blocks:
        if block.name == "say:duration:elapsed:from:":
            lines.append("yield from self.sayfor({}, {})".format(*map(convert_reporters, block.args)))
        elif block.name == "wait:elapsed:from":
            lines.append("yield from self.wait({})".format(*map(convert_reporters, block.args)))
        elif block.name == "doAsk":
            lines.append("yield from self.ask({})".format(*map(convert_reporters, block.args)))
        elif block.name == "doForever":
            lines.append("while True:\n{}\n    yield".format(indent(4, convert_blocks(block.args[0]))))
        elif block.name == "doRepeat":
            lines.append("for _ in range({}):\n{}\n    yield".format(convert_reporters(block.args[0]),
                                                          indent(4, convert_blocks(block.args[1]))))
        elif block.name == "doUntil":
            lines.append("while not {}:\n{}\n    yield".format(convert_reporters(block.args[0]),
                                                          indent(4, convert_blocks(block.args[1]))))
        elif block.name == "doWaitUntil":
            lines.append("while not {}:\n    yield".format(convert_reporters(block.args[0])))
        elif block.name == "setVar:to:":
            lines.append("self.set_var({}, {})".format(*map(convert_reporters, block.args)))
        elif block.name == "changeVar:by:":
            lines.append("self.change_var({}, {})".format(*map(convert_reporters, block.args)))
        elif block.name == "call":
            func = block.args[0].replace("%", "").replace(" ", "_")
            args = ", ".join(map(convert_reporters, block.args[1:]))
            lines.append("yield from self.{}({})".format(func, args))
        elif block.name == "doIfElse":
            pred = convert_reporters(block.args[0])
            if_clause, else_clause = map(convert_blocks, block.args[1:])
            lines.append("if {}:\n{}\nelse:\n{}".format(pred,
                                                        indent(4, if_clause),
                                                        indent(4, else_clause)))
        elif block.name == "doIf":
            pred = convert_reporters(block.args[0])
            if_clause = convert_blocks(block.args[1])
            lines.append("if {}:\n{}".format(pred, indent(4, if_clause)))
    if lines:
        return "\n".join(lines)
    else:
        return "pass"

def convert_reporters(block):
    if isinstance(block, (str, int, float, bool)):
        return repr(block)
    elif block.name in ("+", "-", "*", "/", "%"):
        return "convert_and_run_math({}, {}, {})".format(
                                   repr(block.name),
                                   convert_reporters(block.args[0]),
                                   convert_reporters(block.args[1]))
    elif block.name in ("=", ">", "<"):
        return "convert_and_run_comp({}, {}, {})".format(
                                    repr(block.name),
                                    convert_reporters(block.args[0]),
                                    convert_reporters(block.args[1])
        )
    elif block.name in ("&", "|"):
        op = {"&": "and", "|":"or"}[block.name]
        return "({} {} {})".format(convert_reporters(block.args[0]),
                                   op,
                                   convert_reporters(block.args[1]))
    elif block.name == "not":
        return "(not {})".format(convert_reporters(block.args[0]))
    elif block.name == "concatenate:with:":
        return "(str({}) + str({}))".format(*map(convert_reporters, block.args))
    elif block.name == "answer":
        return "self.answer()"
    elif block.name == "readVariable":
        return "self.get_var({})".format(repr(block.args[0]))
    elif block.name == "getParam":
        return block.args[0]

def transpile(in_, out):
    "Transpiles the .sb2 file found at in_ into a .py which is then written to out"
    objects = get_stage_and_sprites(get_json(in_))
    py = sprites_to_py(objects, out)
    with open(out, "w") as f:
        f.write(py)

if __name__ == '__main__':
    import sys
    transpile(sys.argv[1], sys.argv[2])
