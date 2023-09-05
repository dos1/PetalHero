import media, math
from st3m.ui.colours import *
from st3m.input import InputController
from st3m.ui.view import ViewTransitionSwipeLeft
from st3m.application import Application, ApplicationContext
import st3m.run
import leds
import time
import bl00mbox

# TODO: FIXME
import sys
sys.path.append('/flash/apps/PetalHero')

import song
import flower
import utils

class PetalHero(Application):
    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)
        self.input = InputController()
        self.path = getattr(app_ctx, 'bundle_path', '/flash/apps/PetalHero')
        if not self.path:
            self.path = '/flash/apps/PetalHero'

        self.flower = flower.Flower(0, 0, 0.01)
        self.time = 0
        self.repeats = 0

        self.blm = bl00mbox.Channel("Petal Hero")

        self.in_sound = self.blm.new(bl00mbox.patches.sampler, self.path + "/in.wav")
        self.in_sound.signals.output = self.blm.mixer

        self.out_sound = self.blm.new(bl00mbox.patches.sampler, self.path + "/out.wav")
        self.out_sound.signals.output = self.blm.mixer

        self.crunch_sound = []
        for i in range(3):
            self.crunch_sound.append(self.blm.new(bl00mbox.patches.sampler, self.path + "/crunch" + str(i+1) + ".wav"))
            self.crunch_sound[i].signals.output = self.blm.mixer

    def draw(self, ctx: Context):
        ctx.linear_gradient(-120, -120, 120, 120)

        ctx.add_stop(0.0, [94, 0, 0], 1.0)
        ctx.add_stop(1.0, [51, 0, 0], 1.0)

        ctx.rectangle(-120, -120, 240, 240)
        ctx.fill()

        ctx.save()
        ctx.translate(0, -10)

        ctx.rgba(0.1, 0.4, 0.3, 0.42)
        self.flower.draw(ctx)

        ctx.linear_gradient(-50, 0, 50, 0)
        ctx.add_stop(0.0, [145, 37, 0], 1.0)
        ctx.add_stop(0.5, [245, 111, 0], 0.75)
        ctx.add_stop(1.0, [151, 42, 0], 1.0)

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
        ctx.text("Press the button...")

    def think(self, ins: InputState, delta_ms: int) -> None:
        self.input.think(ins, delta_ms)
        media.think(delta_ms)

        for c in [self.flower]:
            c.rot += float(delta_ms) * c.rot_speed
        self.time += delta_ms / 1000

        if self.time // 18 > self.repeats and self.repeats >= 0:
            media.load(self.path + '/menu.mp3')
            self.repeats += 1

        if self.input.buttons.app.middle.pressed:
            self.in_sound.signals.trigger.start()
            self.vm.push(song.SongView(self), ViewTransitionSwipeLeft())

        if self.input.buttons.os.middle.pressed:
            self.out_sound.signals.trigger.start()

        if self.exiting:
            return

        #leds.set_brightness(32 - int(math.cos(self.time) * 32))
            
        led = -3
        for col in [RED, (1.0, 1.0, 0.0), BLUE, PUSH_RED, GO_GREEN]:
            for i in range(7):
                leds.set_rgb(led if led >= 0 else led + 40, *utils.dim(col, -math.cos(self.time) / 2 + 0.5))
                led += 1
            leds.set_rgb(led, 0, 0, 0)
            led += 1
            
        leds.update()

    def on_enter(self, vm) -> None:
        super().on_enter(vm)
        #self._vm = vm
        # Ignore the button which brought us here until it is released
        #self.input._ignore_pressed()
        media.load(self.path + '/menu.mp3')
        self.repeats = 0
        self.time = 0
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
