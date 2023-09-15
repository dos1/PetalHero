import math
from st3m.ui.colours import *
from st3m.ui.view import ViewTransitionSwipeLeft
from st3m.application import Application, ApplicationContext
import st3m.run
import leds
import bl00mbox
from time import sleep
UNSUPPORTED = False
try:
    import media
    from st3m.ui.view import ViewTransitionDirection
except ImportError:
    UNSUPPORTED = True

# TODO: FIXME
import sys
sys.path.append('/flash/apps/PetalHero')

import flower
import utils
import select
import readme

class PetalHero(Application):
    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)
        self.app = self
        self.path = app_ctx.bundle_path

        self.flower = flower.Flower(0.00125)
        self.loaded = False
        self.blm = None
        self.fiba_sound = None
        self.select = select.SelectView(self.app)
        self.after_score = False
        #self.blm_extra = bl00mbox.Channel("Petal Hero Extra")
        #self.blm_extra.background_mute_override = True

        readme.install()

    def load(self):
        if self.loaded:
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
        if self.app.fiba_sound:
            return

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
        ctx.translate(0, -10)

        ctx.rgba(0.1, 0.4, 0.3, 0.42)
        self.flower.draw(ctx)

        utils.fire_gradient(ctx)

        #ctx.rgb(0.1, 0.4, 0.3)
        ctx.font = "Camp Font 2"
        ctx.font_size = 90
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.move_to (0, -30)
        ctx.text("PETAL")
        ctx.move_to (0, 30)
        ctx.text("HERO")

        ctx.restore()

        ctx.font = "Camp Font 3"
        ctx.font_size = 16
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.gray(1.0)
        ctx.move_to(0, 70 + math.sin(self.time * 4) * 4)
        ctx.text(f"Press the button...") # {sys_display.fps():.2f}")

    def unload(self):
        if not self.loaded:
            return
        self.blm.foreground = False
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

        if self.time < 0:
            self.time = 0
        else:
            self.time += delta_ms / 1000

        if not self.is_active():
            return

        if media.get_time() >= 17.92 or media.get_position() == media.get_duration():
            #media.seek(0)
            media.load(self.path + '/sounds/menu.mp3')

        #leds.set_brightness(32 - int(math.cos(self.time) * 32))
        leds.set_all_rgb(0, 0, 0)

        for i in range(5):
            utils.petal_leds(i, -math.cos(self.time) / 2 + 0.5)

        leds.update()

        if self.input.buttons.app.middle.pressed:
            utils.play_go(self.app)
            self.vm.push(self.select, ViewTransitionSwipeLeft())

    def on_enter(self, vm) -> None:
        super().on_enter(vm)
        if UNSUPPORTED:
            return
        if not self.loaded:
            self.load()
        media.load(self.path + '/sounds/menu.mp3')
        self.time = -1
        leds.set_brightness(69)

    def on_exit(self):
        super().on_exit()
        if UNSUPPORTED:
            return
        media.stop()
        leds.set_all_rgb(0, 0, 0)
        leds.set_brightness(69)
        leds.update()
        if self.vm.direction == ViewTransitionDirection.BACKWARD:
            utils.play_back(self.app)
            
    def on_exit_done(self):
        if UNSUPPORTED:
            return
        if self.vm.direction == ViewTransitionDirection.BACKWARD:
            sleep(0.4)
            self.unload()

if __name__ == '__main__':
    for i in range(1,32):
        bl00mbox.Channel(i).clear()
        bl00mbox.Channel(i).free = True
    st3m.run.run_app(PetalHero, '/flash/apps/PetalHero')
