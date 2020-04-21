import edit

import pygame

def make_menu():
    from model.cls import Class, CallField, Instance, Error
    from model.clsnodes import Field, ClassCall, Constant
    from model import magic_func
    
    @magic_func(['_a', '_b'], ['='])
    def add(a, b):
        return (a+b, )
    add.label = '+'
    @magic_func(['_a', '_b'], ['='])
    def multiply(a, b):
        return (a*b, )
    multiply.label = 'x'
    @magic_func(['condition', 'iftrue', 'iffalse'], ['='], requires_all=False)
    def choose(condition, iftrue, iffalse):
        return (iftrue if condition else iffalse,)
    @magic_func(['_a', '_b'], ['='])
    def equals(a, b):
        return (a == b,)
    equals.label = '='
    
    a = Field('a')
    b = Field('b')
    n = Constant('', -1)
    r = Field('=')
    callmul = ClassCall(multiply)
    calladd = ClassCall(add)
    nodes = [a, b, n, r, callmul, calladd]
    subtract = Class('-', nodes)
    subtract.link(b, CallField(callmul, multiply.fields['a']))
    subtract.link(n, CallField(callmul, multiply.fields['b']))
    subtract.link(a, CallField(calladd, add.fields['a']))
    subtract.link(CallField(callmul, multiply.fields['=']), CallField(calladd, add.fields['b']))
    subtract.link(CallField(calladd, add.fields['=']), r)
    callsubtract = ClassCall(subtract)
    editables = [
        callsubtract,
        calladd,
        callmul,
        ClassCall(choose),
        ClassCall(equals),
        Constant('constant', 0),
        Field('field'),
    ]
    menuclass = Class('menu', editables)
    menu = Instance(menuclass)
    menu[callsubtract] = obj = Instance(subtract, (menu, callsubtract))
    obj[a] = 10
    obj[b] = 3
    return menu

def iter_events():
    return pygame.event.get()

def main():
    resolution = (800, 600)
    screen = pygame.display.set_mode(resolution)
    menu = make_menu()
    env = edit.Env(menu)
    env.stack.items.append(edit.ObjEdit(env.menu, screen, env))
    clock = pygame.time.Clock()
    while True:
        clock.tick(25)
        for event in iter_events():
            try:                
                if env.handle_event(event):
                    continue
            except edit.QuitEvent:
                return
            if pygame.QUIT == event.type:
                return
        env.draw()
        pygame.display.update()

pygame.init()
try:
    main()
finally:
    pygame.quit()
