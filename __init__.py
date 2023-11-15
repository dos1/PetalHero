import os, sys

DEFAULT_PATH = '/flash/apps/PetalHero'

if __name__ == '__main__':
    __path__, __name__ = os.path.split(DEFAULT_PATH)
    sys.path.append(__path__)
    __path__ = None

import math
from st3m.ui.interactions import ScrollController
from st3m.ui.colours import *
from st3m.ui.view import ViewTransitionSwipeLeft
from st3m.application import Application, ApplicationContext
from st3m.input import InputState
from ctx import Context
import st3m.run
import st3m.settings
import leds
import bl00mbox
import time
import sys_display
import _thread

UNSUPPORTED = False
try:
    import media
    from st3m.ui.view import ViewTransitionDirection, ViewTransitionNone
except ImportError:
    UNSUPPORTED = True

from . import utils
if not UNSUPPORTED:
    from . import flower
    from . import select
    from . import readme
    
led_lock = _thread.allocate_lock()
blm_lock = _thread.allocate_lock()

def led_thread(app):
    start = time.ticks_ms()
    while app.is_active():
        if led_lock.acquire(0):
            leds.set_all_rgb(0, 0, 0)
            for i in range(5):
                utils.petal_leds(i, pow(-math.cos((time.ticks_ms() - start) / 1000) / 2 + 0.5, 1 / 2.2))
            leds.update()
            led_lock.release()
        time.sleep_ms(25)
            
def blm_thread(app, num):
    time.sleep(1.0)
    if blm_lock.acquire(1):
        if app.unloading == num:
            app.unloading = 0
            app.unload()
        blm_lock.release()

class PetalHero(Application):
    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)
        self.app = self
        if UNSUPPORTED:
            return

        self.path = app_ctx.bundle_path

        self.flower = flower.Flower(0.00125)
        self.loaded = False
        self.blm = None
        self.fiba_sound = None
        self.after_score = False
        self.select = select.SelectView(self.app)
        #self.blm_extra = bl00mbox.Channel("Petal Hero Extra")
        #self.blm_extra.background_mute_override = True
        
        self.blm_timeout = 1
        self.unloading = 0
        self.unloading_num = 1
        
        self.sc = ScrollController()
        self.sc.set_item_count(2)
        self.show_artist = False
        self.reentry = False

    #def show_icons(self): return True

    def load(self):
        blm_lock.acquire(1)
        self.unloading = 0
        blm_lock.release()

        if self.loaded:
            self.blm.foreground = True
            return

        self.blm = bl00mbox.Channel("Petal Hero")
        self.blm.volume = 14000

        self.app.in_sound = self.blm.new(bl00mbox.patches.sampler, self.path + "/sounds/in.wav")
        self.app.in_sound.signals.output = self.blm.mixer

        self.app.out_sound = self.blm.new(bl00mbox.patches.sampler, self.path + "/sounds/out.wav")
        self.app.out_sound.signals.output = self.blm.mixer

        self.app.crunch_sound = []
        for i in range(3):
            self.app.crunch_sound.append(self.blm.new(bl00mbox.patches.sampler, self.path + "/sounds/crunch" + str(i+1) + ".wav"))
            self.app.crunch_sound[i].signals.output = self.blm.mixer

        self.loaded = True

    def load_fiba(self):
        if not self.loaded:
            return

        if self.app.fiba_sound:
            return
        
        utils.blm_wake(self, 1)

        self.app.fiba_sound = []
        for i in range(6):
            self.app.fiba_sound.append(self.blm.new(bl00mbox.patches.sampler, self.path + "/sounds/fiba" + str(i+1) + ".wav"))
            self.app.fiba_sound[i].signals.output = self.blm.mixer

    def draw(self, ctx: Context):
        if UNSUPPORTED:
            utils.clear(ctx)
            ctx.font = "Camp Font 3"
            ctx.text_align = ctx.CENTER
            ctx.text_baseline = ctx.MIDDLE
            ctx.gray(1)
            ctx.font_size = 22
            ctx.move_to(0, -30)
            ctx.text("Petal Hero requires")
            ctx.move_to(0,-4)
            ctx.text("firmware 1.3.0 or later.")
            ctx.move_to(0,24)
            ctx.font_size = 16
            ctx.text("Please upgrade and try again.")
            return
            
        utils.background(ctx)

        ctx.save()
        ctx.translate(-240 * self.sc.current_position(), 0)

        if self.sc.current_position() < 1.0:
            ctx.save()
            ctx.translate(0, -10)

            ctx.rgba(0.1, 0.4, 0.3, 0.42)
            self.flower.draw(ctx)

            utils.fire_gradient(ctx)

            #ctx.rgb(0.1, 0.4, 0.3)
            ctx.font = "Camp Font 2"
            ctx.font_size = 90
            ctx.text_align = ctx.CENTER
            ctx.text_baseline = ctx.MIDDLE
            ctx.move_to (0, -28)
            ctx.text("PETAL")
            ctx.move_to (0, 28)
            ctx.text("HERO")

            ctx.restore()

            ctx.font = "Camp Font 3"
            ctx.font_size = 16
            ctx.text_align = ctx.CENTER
            ctx.text_baseline = ctx.MIDDLE
            ctx.gray(1.0)
            ctx.move_to(0, 74 + math.sin(self.time * 4) * 4)
            ctx.text(f"Press the button...") # {sys_display.fps():.2f}")

            if self.is_active():
                ctx.rgba(1.0, 1.0, 1.0, 0.33 * (1- self.sc.current_position()))
                ctx.text_align = ctx.CENTER
                ctx.text_baseline = ctx.MIDDLE
                ctx.move_to(105, 4)
                ctx.font = "Material Icons"
                ctx.font_size = 18
                ctx.text("\ue5c8")

        if self.sc.current_position() > 0.0:
            ctx.translate(240, 0)

            ctx.save()
            ctx.translate(0, -85)
            ctx.scale(0.333, 0.333)
            ctx.rgba(0.1, 0.4, 0.3, 0.42)
            self.flower.draw(ctx)
            ctx.restore()

            utils.fire_gradient(ctx)

            #ctx.rgb(0.1, 0.4, 0.3)
            ctx.font = "Camp Font 2"
            ctx.font_size = 32
            ctx.text_align = ctx.CENTER
            ctx.text_baseline = ctx.MIDDLE
            ctx.move_to (0, -85)
            ctx.text("PETAL HERO")
            
            ctx.gray(0.75)
            ctx.font = "Camp Font 3"
            ctx.font_size = 14
            ctx.move_to(0, -63)
            ctx.text(f"Version {utils.VERSION}")
            
            ctx.font_size = 16
            ctx.move_to(0, -35)
            ctx.text("Made by")
            ctx.move_to(0, -18)
            ctx.gray(1.0)
            ctx.text("dos" if self.show_artist else "Sebastian Krzyszkowiak")

            ctx.rgb(0.102, 0.09, 0.094)
            ctx.rectangle(-119 - int(self.sc.current_position()), 0, 479 + int(self.sc.current_position()), 1)
            ctx.fill()

            ctx.rgb(0.137, 0.122, 0.125)            
            if self.sc.current_position() > 1.0:
                """
                ctx.linear_gradient(0, 0, 1, 1)
                ctx.add_stop(0.0, (0.137, 0.122, 0.125), 1.0)
                ctx.add_stop(1.0, (0.102, 0.09, 0.094), 1.0)
                """
                ctx.rectangle(-120, 1, 480, 60)
            elif self.sc.current_position() == 1.0:
                ctx.rectangle(-120, 1, 240, 25)
            ctx.fill()

            ctx.rgb(0.102, 0.09, 0.094)
            ctx.rectangle(-119, 60, 479, 1)
            ctx.fill()

            ctx.image_smoothing = False
            ctx.image(self.path + ("/img/dosowisko1.png" if (time.ticks_ms() // 500) % 2 else "/img/dosowisko2.png"), -120, 0, -1, -1)

            if self.sc.current_position() < 1.0:
                ctx.rgb(0.102, 0.09, 0.094)
                ctx.rectangle(-119, 0, 1, 61)
                ctx.fill()

            ctx.gray(0.75)
            ctx.move_to(0, 78)
            ctx.text("Licensed under GPLv3")

            ctx.font_size = 15
            ctx.move_to(0, 102)
            ctx.text("© 2023")

            ctx.rgba(1.0, 1.0, 1.0, 0.33 * self.sc.current_position())
            ctx.text_align = ctx.CENTER
            ctx.text_baseline = ctx.MIDDLE
            ctx.move_to(-105, 4)
            ctx.font = "Material Icons"
            ctx.font_size = 18
            ctx.text("\ue5c4")

        ctx.restore()

    def unload(self):
        if not self.loaded:
            return
        self.blm.foreground = False
        self.blm.clear()
        self.blm.free = True
        self.blm = None
        self.loaded = False
        self.in_sound = None
        self.out_sound = None
        self.crunch_sound = None
        self.fiba_sound = None

    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)
        if UNSUPPORTED:
            return

        media.think(delta_ms)
        self.flower.think(delta_ms)
        utils.blm_timeout(self, delta_ms)
        self.sc.think(ins, delta_ms)

        if self.time < 0:
            self.time = 0
        else:
            self.time += delta_ms / 1000

        if self.input.buttons.os.middle.pressed and self.sc.target_position() == 1:
            self.vm.push(self, ViewTransitionNone())
            self.sc.scroll_to(0)
            utils.play_crunch(self.app)
            self.reentry = True

        if not self.is_active():
            return

        if media.get_position() == media.get_duration():
            media.seek(0)

        #leds.set_brightness(32 - int(math.cos(self.time) * 32))

        if self.input.buttons.app.middle.pressed:
            utils.play_go(self.app)
            self.vm.push(self.select, ViewTransitionSwipeLeft())
            
        if self.input.buttons.app.left.pressed:
            utils.play_crunch(self.app)
            self.sc.scroll_left()

        if self.input.buttons.app.right.pressed:
            utils.play_crunch(self.app)
            self.sc.scroll_right()
            
        if not self.vm.transitioning:
            self.select.discover(20, False)
            
        self.show_artist = ins.captouch.petals[5].pressed

    def on_enter(self, vm) -> None:
        super().on_enter(vm)
        if UNSUPPORTED:
            return
        if self.reentry:
            self.reentry = False
            return
        if self.vm.direction == ViewTransitionDirection.FORWARD:
            readme.install()
            if self.select:
                self.select.refresh()
        self.load()
        media.set_volume(1.0)
        media.load(self.path + '/sounds/menu.mp3')
        self.time = -1
        led_lock.acquire(1)
        leds.set_all_rgb(0, 0, 0)
        leds.update()
        led_lock.release()
        leds.set_slew_rate(255)
        leds.set_gamma(2.2, 2.2, 2.2)
        leds.set_auto_update(False)
        leds.set_brightness(int(pow(st3m.settings.num_leds_brightness.value / 255, 1/2.2) * 255))
        self.sc.set_position(0.0)
        _thread.start_new_thread(led_thread, (self,))

    def on_enter_done(self):
        leds.set_slew_rate(42)

    def on_exit(self):
        super().on_exit()
        if UNSUPPORTED or self.reentry:
            return
        media.stop()
        led_lock.acquire(1)
        leds.set_all_rgb(0, 0, 0)
        leds.update()
        led_lock.release()
        if self.vm.direction == ViewTransitionDirection.BACKWARD:
            utils.play_back(self.app)
            self.unloading = self.unloading_num
            self.unloading_num += 1
            _thread.start_new_thread(blm_thread, (self, self.unloading))
        return True
            
if not __path__:
    for i in range(1,32):
        bl00mbox.Channel(i).clear()
        bl00mbox.Channel(i).free = True
    st3m.run.run_app(PetalHero, DEFAULT_PATH)
