import ast
import asyncio
import time
from threading import Thread


def target(n):
    a = n + 15
    b = n + 2
    c = a * b
    yield c
    yield b


def getmaxloc(node):
    loc = None
    for node_ in ast.walk(node):
        if not hasattr(node_, 'lineno') or not hasattr(node_, 'col_offset'):
            continue
        loc_ = (node_.lineno, node_.col_offset)
        if loc is None or loc_ > loc:
            loc = loc_
    return loc


class Yieldifier(ast.NodeTransformer):
    def __init__(self):
        ast.NodeTransformer.__init__(self)
        self.added = 0

    def generic_visit(self, node):
        ast.NodeTransformer.generic_visit(self, node)
        if isinstance(node, ast.stmt):
            self.added += 1
            return [node, ast.Expr(value=ast.Yield(value=ast.Str(n=f"__yieldline__{self.added}")), lineno=getmaxloc(node)[0])]
        else:
            return node


def yieldify(path, func_name):
    with open(path, 'rb') as f:
        source = f.read()

    mod_tree = ast.parse(source, path)
    func_trees = {obj.name: obj for obj in mod_tree.body if isinstance(obj, ast.FunctionDef)}
    func_tree = func_trees[func_name]

    Yieldifier().visit(func_tree)
    ast.fix_missing_locations(func_tree)

    env = {}
    exec(compile(mod_tree, path, 'exec'), env)
    return env[func_name]


def process_handler():
    global resume
    while True:
        resume = yield


async def tasky():
    global resume
    line_iter = func(1)
    while resume:
        try:
            print(next(line_iter))
            time.sleep(1)
        except StopIteration:
            print("execution finished")


async def main():
    asyncio.create_task(tasky())


if __name__ == '__main__':
    func = yieldify(__file__, 'target')
    resume = True
    handler = process_handler()
    handler.send(None)
    t = Thread(target=lambda coro: asyncio.run(coro()), args=(main,))
    t.start()
    time.sleep(4)  # change the seconds to observe.
    handler.send(False)  # remove this line to be sure that it stops the function execution.
