from st3m.ui.colours import *
import leds
import random
import os
import time
import sys
import sys_bl00mbox
try:
    from st3m.utils import sd_card_plugged as sd_card_present
except ImportError:
    sd_card_present = lambda: False
try:
    import _ph
except ImportError:
    _ph = None

VERSION = "1.1"

SONGS_REPO = "https://git.flow3r.garden/dos/PetalHero-songs"
# alternative url: "https://gitlab.com/dosowisko.net/PetalHero-songs"

def dim(color, val):
    res = []
    for i in range(len(color)):
        res.append(color[i] * val)
    return res

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

PETAL_COLORS = [GO_GREEN, RED, (1.0, 0.8, 0.0), BLUE, PUSH_RED]

def petal_leds(petal, val, color = None):
    if not color:
        color = PETAL_COLORS[petal]
    color = dim(color, val)
    for i in range(7):
        led = i - 11 + petal * 8
        if led < 0:
            led += 40
        leds.set_rgb(led, *color)

def blm_wake(app, timeout):
    if not app or not app.loaded: return
    if app.blm_timeout == 0 and sys_bl00mbox.channel_enable:
        try:
            sys_bl00mbox.channel_enable(app.blm.channel_num)
        except Exception as e:
            sys.print_exception(e)
    if timeout > app.blm_timeout:
        app.blm_timeout = timeout

def blm_timeout(view, delta_ms):
    app = view.app
    if not app: return
    if not view.is_active(): return
    if app.blm_timeout == 0: return
    app.blm_timeout -= delta_ms
    if app.blm_timeout <= 0 and sys_bl00mbox.channel_disable:
        try:
            sys_bl00mbox.channel_disable(app.blm.channel_num)
        except Exception as e:
            sys.print_exception(e)
        app.blm_timeout = 0

def play_crunch(app):
    if not app: return
    if not app.crunch_sound:
        return
    app.crunch_sound[random.randint(0, 2)].signals.trigger.start()
    blm_wake(app, 600)

def play_fiba(app):
    if not app: return
    if not app.fiba_sound:
        return
    app.fiba_sound[random.randint(0, 5)].signals.trigger.start()
    blm_wake(app, 1400)

def play_go(app):
    if not app or not app.loaded: return
    app.in_sound.signals.trigger.start()
    blm_wake(app, 1200)

def play_back(app):
    if not app or not app.loaded: return
    app.out_sound.signals.trigger.start()
    blm_wake(app, 800)

def circle(ctx, x, y, r):
    c = 0.55191502449
    ctx.begin_path()
    ctx.move_to(x - r, y);
    ctx.curve_to(x - r, y - (c * r), x - (c * r), y - r, x, y - r)
    ctx.curve_to(x + (c * r), y - r, x + r, y - (c * r), x + r, y)
    ctx.curve_to(x + r, y + (c * r), x + (c * r), y + r, x, y + r)
    ctx.curve_to(x - (c * r), y + r, x - r, y + (c * r), x - r, y)
    ctx.stroke()

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = f(*args, **kwargs)
        delta = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

def volume(app, vol):
    if app and app.loaded:
        app.blm.volume = vol

def emit(*args, **kwargs):
    if _ph and _ph.emit:
        _ph.emit(*args, **kwargs)
