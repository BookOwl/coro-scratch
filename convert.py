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
        return list(self.__data.keys())
    def __getattr__(self, attr):
        return JSON_Wrap(self._data[attr])

Sprite = collections.namedtuple("Sprite", "name scripts")
Block = collections.namedtuple("Block", "name args")

def get_json(path):
    "Extracts the json from a .sb2 file"
    with zipfile.ZipFile(path, 'r') as project:
        with project.open("project.json", "r") as data:
            return JSON_Wrap(json_.loads(data.read().decode()))

def get_sprites(json):
    "Extracts the sprites from json"
    def convert(script):
        if isinstance(script, list):
            name, *args = script
            return Block(name, [convert(arg) for arg in args])
        return script
    sprites = []
    for child in json.children:
        name = child.objName
        scripts = []
        for script in child.scripts:
            script = script[2]
            scripts.append([convert(block) for block in script])
        sprites.append(Sprite(name, scripts))
    return sprites

def indent(amount, code):
    return "\n".join(" "*amount + line for line in code.split("\n"))

def sprites_to_py(sprites, name):
    "Converts the sprites to a .py file"
    header = """#! usr/bin/env python3
# {}.py

import asyncio
import runtime

loop = asyncio.get_event_loop()

""".format(name)

    footer = """

def main():
    tasks = [asyncio.ensure_future(script()) for script in runtime.greenflags]
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()

main()"""

    converted_sprites = [convert_sprite(sprite) for sprite in sprites]
    return header + '\n\n'.join(converted_sprites) + footer

def convert_sprite(sprite):
    "Converts the sprite to a class"
    class_template = """@runtime.create_sprite
class {}(runtime.Sprite):
{}"""
    gf_template = """@asyncio.coroutine
def greenflag{}(self):
{}"""
    funcs = []
    greenflags = 0
    for script in sprite.scripts:
        hat, *blocks = script
        if hat.name == "whenGreenFlag":
            greenflags += 1
            funcs.append(gf_template.format(greenflags, indent(4, convert_blocks(blocks))))
    return class_template.format(sprite.name, indent(4, "\n\n".join(funcs)))

def convert_blocks(blocks):
    lines = []
    for block in blocks:
        if block.name == "say:duration:elapsed:from:":
            lines.append("yield from self.sayfor({}, {})".format(*map(convert_reporters, block.args)))
        elif block.name == "wait:elapsed:from":
            lines.append("yield from self.wait({})".format(*map(convert_reporters, block.args)))
        elif block.name == "doAsk":
            lines.append("yield from self.ask({})".format(*map(convert_reporters, block.args)))
    return "\n".join(lines)

def convert_reporters(block):
    if isinstance(block, (str, int, float)):
        return repr(block)
    elif block.name in ("+", "-", "*", "/"):
        return "({} {} {})".format(convert_reporters(block.args[0]),
                                   block.name,
                                   convert_reporters(block.args[1]))
    elif block.name == "concatenate:with:":
        return "(str({}) + str({}))".format(*map(convert_reporters, block.args))
    elif block.name == "answer":
        return "self.answer()"

def transpile(in_, out):
    "Transpiles the .sb2 file found at in_ into a .py which is then written to out"
    sprites = get_sprites(get_json(in_))
    py = sprites_to_py(sprites, out)
    with open(out, "w") as f:
        f.write(py)

if __name__ == '__main__':
    import sys
    #json = get_json("test2.sb2")
    #sprites = get_sprites(json)
    #print("\n\n".join(map(str, sprites[0].scripts)))
    transpile(sys.argv[1], sys.argv[2])
