from st3m.ui.colours import *
import leds
import random

dim = lambda x, y: tuple(map(lambda x: x * y, x))

def background(ctx):
    ctx.linear_gradient(-120, -120, 120, 120)

    ctx.add_stop(0.0, [94, 0, 0], 1.0)
    ctx.add_stop(1.0, [51, 0, 0], 1.0)

    ctx.rectangle(-120, -120, 240, 240)
    ctx.fill()

def clear(ctx, color = 0):
    if type(color) in (float, int):
        ctx.gray(color)
    else:
        ctx.rgb(*color)
    ctx.rectangle(-120, -120, 240, 240)
    ctx.fill()

def fire_gradient(ctx):
    ctx.linear_gradient(-50, 0, 50, 0)
    ctx.add_stop(0.0, [145, 37, 0], 1.0)
    ctx.add_stop(0.5, [245, 111, 0], 0.75)
    ctx.add_stop(1.0, [151, 42, 0], 1.0)

PETAL_COLORS = [GO_GREEN, RED, (1.0, 0.69, 0.0), BLUE, PUSH_RED]

def petal_leds(petal, val, color = None):
    if not color:
        color = PETAL_COLORS[petal]
    color = dim(color, val)
    start = -11 + petal * 8
    for i in range(start, start + 7):
        led = i
        if led < 0:
            led += 40
        leds.set_rgb(led, *color)

def play_crunch(app):
    if not app: return
    if not app.crunch_sound:
        return
    app.crunch_sound[random.randint(0, 2)].signals.trigger.start()

def play_fiba(app):
    if not app: return
    if not app.fiba_sound:
        return
    app.fiba_sound[random.randint(0, 5)].signals.trigger.start()

def play_go(app):
    if not app: return
    app.in_sound.signals.trigger.start()

def play_back(app):
    if not app: return
    app.out_sound.signals.trigger.start()

def circle(ctx, x, y, r):
    c = 0.55191502449
    ctx.begin_path()
    ctx.move_to(x - r, y);
    ctx.curve_to(x - r, y - (c * r), x - (c * r), y - r, x, y - r)
    ctx.curve_to(x + (c * r), y - r, x + r, y - (c * r), x + r, y)
    ctx.curve_to(x + r, y + (c * r), x + (c * r), y + r, x, y + r)
    ctx.curve_to(x - (c * r), y + r, x - r, y + (c * r), x - r, y)
    ctx.stroke()
