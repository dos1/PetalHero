import media, math
from st3m.ui.colours import *
from st3m.input import InputController
from st3m.ui.view import ViewTransitionSwipeLeft
from st3m.application import Application, ApplicationContext
import st3m.run
import leds
import time
import bl00mbox
import sys_display

# TODO: FIXME
import sys
sys.path.append('/flash/apps/PetalHero')

import flower
import utils
import select

class PetalHero(Application):
    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)
        self.app = self
        self.path = getattr(app_ctx, 'bundle_path', '/flash/apps/PetalHero')
        if not self.path:
            self.path = '/flash/apps/PetalHero'

        self.flower = flower.Flower(0.00125)
        self.loaded = False
        self.blm = None
        self.fiba_sound = None
        self.select = select.SelectView(self.app)
        #self.blm_extra = bl00mbox.Channel("Petal Hero Extra")
        #self.blm_extra.background_mute_override = True

    def load(self):
        if self.loaded:
            return

        self.blm = bl00mbox.Channel("Petal Hero")
        self.blm.volume = 14000

        self.app.in_sound = self.blm.new(bl00mbox.patches.sampler, self.path + "/in.wav")
        self.app.in_sound.signals.output = self.blm.mixer

        self.app.out_sound = self.blm.new(bl00mbox.patches.sampler, self.path + "/out.wav")
        self.app.out_sound.signals.output = self.blm.mixer

        self.app.crunch_sound = []
        for i in range(3):
            self.app.crunch_sound.append(self.blm.new(bl00mbox.patches.sampler, self.path + "/crunch" + str(i+1) + ".wav"))
            self.app.crunch_sound[i].signals.output = self.blm.mixer

        self.loaded = True

    def load_fiba(self):
        if self.app.fiba_sound:
            return

        self.app.fiba_sound = []
        for i in range(6):
            self.app.fiba_sound.append(self.blm.new(bl00mbox.patches.sampler, self.path + "/fiba" + str(i+1) + ".wav"))
            self.app.fiba_sound[i].signals.output = self.blm.mixer

    def draw(self, ctx: Context):
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
        if not self.loaded or not self.exiting:
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
        media.think(delta_ms)
        self.flower.think(delta_ms)

        if self.time < 0:
            self.time = 0
        else:
            self.time += delta_ms / 1000

        #if media.get_position() == media.get_duration():
        #    media.seek(0)
        #print(media.get_position(), media.get_duration(), media.get_time())
          
        if self.time // 18 > self.repeats and self.repeats >= 0:
            media.load(self.path + '/menu.mp3')
            self.repeats += 1

        if self.input.buttons.app.middle.pressed:
            utils.play_go(self.app)
            self.vm.push(self.select, ViewTransitionSwipeLeft())
            self.select.play()

        if self.input.buttons.os.middle.pressed:
            utils.play_back(self.app)
            self.unload()

        if self.exiting:
            return

        #leds.set_brightness(32 - int(math.cos(self.time) * 32))
        leds.set_all_rgb(0, 0, 0)

        for i in range(5):
            utils.petal_leds(i, -math.cos(self.time) / 2 + 0.5)

        leds.update()

    def on_enter(self, vm) -> None:
        super().on_enter(vm)
        if not self.loaded:
            self.load()
        #self._vm = vm
        # Ignore the button which brought us here until it is released
        #self.input._ignore_pressed()
        media.load(self.path + '/menu.mp3')
        self.repeats = 0
        self.time = -1
        self.exiting = False
        leds.set_brightness(69)

    def on_exit(self):
        super().on_exit()
        media.stop()
        self.exiting = True
        leds.set_all_rgb(0, 0, 0)
        leds.set_brightness(69)
        leds.update()

if __name__ == '__main__':
    st3m.run.run_app(PetalHero)
