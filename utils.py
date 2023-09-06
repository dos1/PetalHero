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

def fire_gradient(ctx):
    ctx.linear_gradient(-50, 0, 50, 0)
    ctx.add_stop(0.0, [145, 37, 0], 1.0)
    ctx.add_stop(0.5, [245, 111, 0], 0.75)
    ctx.add_stop(1.0, [151, 42, 0], 1.0)

PETAL_COLORS = [GO_GREEN, RED, (1.0, 0.69, 0.0), BLUE, PUSH_RED]

def petal_leds(petal, val):
    color = dim(PETAL_COLORS[petal], val)
    start = -11 + petal * 8
    for i in range(start, start + 7):
        led = i
        if led < 0:
            led += 40
        leds.set_rgb(led, *color)

def play_crunch(app):
    if not app.crunch_sound:
        return
    app.crunch_sound[random.randint(0, 2)].signals.trigger.start()

def play_fiba(app):
    if not app.fiba_sound:
        return
    app.fiba_sound[random.randint(0, 5)].signals.trigger.start()
