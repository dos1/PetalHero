from st3m.input import InputController
from st3m.ui.view import BaseView, ViewManager, ViewTransitionSwipeRight
from st3m.application import Application, ApplicationContext
from st3m.ui.colours import *
from st3m.utils import tau
import st3m.run
import math
import media
import leds
import sys_display
import gc

if __name__ == '__main__':
    import sys
    sys.path.append('/flash/apps/PetalHero')

import midi
import midireader
import utils
import flower

class SongView(BaseView):
    def __init__(self, app, song, difficulty):
        super().__init__()
        self.app = app
        self.song = song
        self.difficulty = difficulty
        if self.app:
            self.app.load_fiba()
        if self.song:
            self.data = midireader.MidiReader(self.song, self.difficulty)
            midiIn = midi.MidiInFile(self.data, self.song.dirName + '/notes.mid')
            midiIn.read()
        else:
            self.data = midireader.MidiReader(None, None)
            self.data.period = 500
            self.data.bpm = 120
        self.delay = 2000
        self.started = False
        self.time = -self.delay
        self.flower = flower.Flower(0)
        self.events = []
        self.petals = [False] * 5
        self.demo_mode = False
        self.fps = False
        self.debug = False

    def draw(self, ctx: Context) -> None:
        if self.delay < 1500:
            sys_display.set_mode(2)
            
        ctx.compositing_mode = ctx.COPY
        DELAY = 90

        self.time += DELAY
        
        other = int(self.time / 2 / self.data.period) % 2
        if self.time < 0:
            other = not other

        ctx.gray(0.1 if other else 0.0)
        ctx.rectangle(-120, -120, 240, 240)
        ctx.fill()
                
        ctx.gray(0.25)
        
        for i in [1, 0]:
            #ctx.gray(0.4 + i * 0.12 + (1-(self.time/2 / self.data.period) % 1) * 0.12)
            #ctx.line_width = 1.75 + i * 0.12 + (1-(self.time/2 / self.data.period) % 1) * 0.12
            ctx.gray(0.1 if other ^ (i == 1) else 0.0)
            pos = 23*2 * (i+1-(self.time/2 / self.data.period) % 1)
            if pos > 0:
                ctx.begin_path()
                if self.debug:
                    utils.circle(ctx, 0, 0, 28 + pos)
                else:
                    ctx.arc(0, 0, 28 + pos, 0, tau, 0)
                    ctx.fill()
        self.time -= DELAY
        
        ctx.line_width = 2

        ctx.save()
        ctx.gray(0.42)
        ctx.rotate(tau / 5 / 2)
        ctx.begin_path()
        for i in range(5):
            ctx.move_to(0, 0)
            ctx.line_to(0, -120)
            ctx.rotate(tau / 5)
        ctx.stroke()

        ctx.line_width = 3

        ctx.begin_path()
        if not self.debug:
            ctx.gray(0.0)
            ctx.arc(0, 0, 28, 0, tau, 0)
            ctx.fill()
            ctx.gray(0.69)
            ctx.arc(0, 0, 28, 0, tau, 0)
            ctx.stroke()
        else:
            ctx.gray(1.0)
            utils.circle(ctx, 0, 0, 28)
        ctx.restore()
        
        ctx.save()
        ctx.rotate(tau / 10 + tau / 5)
        start = self.time + self.data.period * 4
        stop = self.time
        for i in range(5):
            for time, event in self.events:
                if not isinstance(event, midireader.Note): continue
                if not start >= time >= stop and not start >= (time + event.length) >= stop and not time <= stop <= (time + event.length): continue
                if not event.number == i: continue

                ctx.begin_path()

                length = event.length
                during = False
                arc = tau/20
                if self.demo_mode:
                    time -= DELAY
                if (self.petals[i] or self.demo_mode) and time < self.time and time + length > self.time:
                    length -= self.time - time + DELAY
                    time = self.time
                    orig_time = time
                    during = True
                    arc *= 1.5
                else:
                    orig_time = time
                    if not self.demo_mode:
                        time -= DELAY
                    
                ctx.line_width = 6
                ctx.line_cap = ctx.NONE
                if event.length > 120 or (orig_time < self.time and not during):
                    d = 0.75 if orig_time >= self.time else 0.33
                    if during: d = 1.0
                    ctx.rgb(*utils.dim(utils.PETAL_COLORS[i], d))
                    pos1 = max(0, - (stop - time) / (start - stop) * 92 + 28)
                    pos2 = max(0, - (stop - (time + length)) / (start - stop) * 92 + 28)
                    ctx.rectangle(-3, pos1, 6, pos2-pos1)
                    ctx.fill()
                    #ctx.move_to(0, max(0, - (stop - time) / (start - stop) * 92 + 28))
                    #ctx.line_to(0, max(0, - (stop - (time + length)) / (start - stop) * 92 + 28))
                    #ctx.stroke()
                
                ctx.rgb(*utils.PETAL_COLORS[i])
                pos = - (stop - time) / (start - stop)
                ctx.line_width = 3 + 3 * pos
                
                if pos >= 0: # and not self.debug:
                    ctx.arc(0, 0, pos * 92 + 28, -arc + tau / 4, arc + tau / 4, 0)
                    #ctx.arc(0, 0, max(0, - (stop - (time + length)) / (start - stop) * 120), -tau/40, tau/40, 1)
                    ctx.stroke()

            ctx.rotate(tau / 5)
        ctx.restore()
        
        ctx.line_width = 2

        ctx.save()
        ctx.scale(0.42, 0.42)
        self.time += DELAY
        wiggle = math.cos(((self.time / self.data.period / 2) % 1) * tau) * 0.1
        self.flower.rot = tau / 5 / 2 + wiggle
        ctx.rgb(0.945, 0.631, 0.769)
        self.flower.draw(ctx)
        ctx.restore()
        
        ctx.gray(0.3 * (1.0 - ((((self.time / self.data.period) % 1)**2) * 0.75) if self.started else 0.0))
        ctx.begin_path()
        ctx.arc(0, 0, 10, 0, tau, 0)
        ctx.fill()
        self.time -= DELAY
        
        ctx.save()
        ctx.gray(0.5)
        ctx.scale(0.0625, 0.125 * 0.3)
        ctx.begin_path()
        #ctx.rotate(wiggle)
        if self.started:
            ctx.scope()
            ctx.line_to(120, 0)
            ctx.line_to(-120, 0)
            ctx.fill()
        ctx.restore()
        
        ctx.gray(0.8)
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE

        if self.demo_mode:
            ctx.font = "Camp Font 2"
            ctx.font_size = 30
            ctx.move_to (0, 40)
            ctx.text("DEMO")
            
        if self.fps:
            ctx.font = "Camp Font 3"
            ctx.font_size = 16
            ctx.move_to(0, 105)
            ctx.text(f"{sys_display.fps():.2f}")

    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)
        media.think(delta_ms)
        if self.input.buttons.os.middle.pressed:
            self.vm.pop(ViewTransitionSwipeRight())
        self.delay -= delta_ms
        if delta_ms > 80:
            delta_ms = 56
        #if self.started:
        self.time += delta_ms
        if self.delay < 25 and not self.started:
            self.started = True
            if self.song:
                media.load(self.song.dirName + '/song.mp3')
            #self.time = 0

        if self.input.buttons.app.middle.pressed:
            self.demo_mode = not self.demo_mode

        if self.input.buttons.app.left.pressed:
            self.fps = not self.fps

        if self.input.buttons.app.right.pressed:
            self.debug = not self.debug

        earlyMargin       = 60000.0 / self.data.bpm / 3.5
        lateMargin        = 60000.0 / self.data.bpm / 3.5

        notes = set()
        notes_in_margin = set()
        if self.app:
            self.events = self.data.track.getEvents(self.time - self.data.period * 2, self.time + self.data.period * 4)
        for time, event in self.events:
            if isinstance(event, midireader.Note):
                if time <= self.time <= time + event.length:
                    notes.add(event.number)
                if time - earlyMargin <= self.time <= time + lateMargin:
                    notes_in_margin.add(event.number)

        if not self.started:
            return

        leds.set_all_rgb(0, 0, 0)

        for petal in range(5):
            p = 4 if petal == 0 else petal - 1
            pressed = ins.captouch.petals[p*2].pressed
            active = self.petals[petal]
            d = 1.0 if pressed and active else (0.15 if pressed else (1.0 if petal in notes and self.demo_mode else 0))
            if d:
                utils.petal_leds(petal, d)

            if not pressed:
                self.petals[petal] = False

            if self.input.captouch.petals[p*2].whole.pressed:
                if petal not in notes_in_margin:
                    utils.play_fiba(self.app)
                else:
                    self.petals[petal] = True

        leds.update()

    def on_enter(self, vm: Optional[ViewManager]) -> None:
        super().on_enter(vm)
        #self._vm = vm
        # Ignore the button which brought us here until it is released
        #self.input._ignore_pressed()
        if self.app:
            media.load(self.app.path + '/sounds/start.mp3')
            self.app.blm.volume = 10000
        #gc.disable()

    def on_exit(self):
        sys_display.set_mode(0)
        super().on_exit()
        if self.app:
            self.app.blm.volume = 14000
            utils.play_back(self.app)
        #gc.enable()

if __name__ == '__main__':
    media.stop()
    view = SongView(None, None, None)
    view.fps = True
    st3m.run.run_view(view)
