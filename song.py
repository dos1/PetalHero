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
import score

AUDIO_DELAY = -70
VIDEO_DELAY = 30 - AUDIO_DELAY
RADIUS = 22

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
        self.delay = 2000 + AUDIO_DELAY
        self.started = False
        self.time = -self.delay
        self.flower = flower.Flower(0)
        self.events = []
        self.petals = [None] * 5
        self.demo_mode = False
        self.fps = False
        self.debug = False
        self.successive_sames = 0
        self.finished = False
        self.streak = 0
        self.longeststreak = 0
        self.exiting = False
        self.led_override = [0] * 5
        self.laststreak = -1
        
        self.good = 0.0
        self.bad = 0.0
        self.missed = [0.0] * 5
        self.miss = 0.0

    def draw(self, ctx: Context) -> None:
        mode = sys_display.get_mode()
        if mode == 0:
            mode = 16
        sys_display.set_mode(mode | 512)

        self.time += VIDEO_DELAY
        
        other = int(self.time / 2 / self.data.period) % 2
        if self.time < 0:
            other = not other

        ctx.gray((0.1 if other else 0.0) + self.miss * 0.1)
        ctx.rectangle(-120, -120, 240, 240)
        ctx.fill()
                
        ctx.gray(0.25)
        
        for i in [1, 0]:
            #ctx.gray(0.4 + i * 0.12 + (1-(self.time/2 / self.data.period) % 1) * 0.12)
            #ctx.line_width = 1.75 + i * 0.12 + (1-(self.time/2 / self.data.period) % 1) * 0.12
            ctx.gray((0.1 if other ^ (i == 1) else 0.0) + self.miss * 0.1)
            pos = (120-RADIUS)/2 * (i+1-(self.time/2 / self.data.period) % 1)
            if pos > 0:
                ctx.begin_path()
                if self.debug:
                    utils.circle(ctx, 0, 0, RADIUS + pos)
                else:
                    ctx.arc(0, 0, RADIUS + pos, 0, tau, 0)
                    ctx.fill()
        self.time -= VIDEO_DELAY
        
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
        ctx.restore()

        ctx.line_width = 3

        if not self.debug:
            for i in range(5):
                ctx.gray(math.sqrt(self.missed[i]) * 0.6)
                ctx.begin_path()
                ctx.arc(0, 0, RADIUS, (tau / 5) * (i - 2.25 - 0.5), (tau / 5) * (i - 2.25 + 0.5), 0)
                ctx.line_to(0, 0)
                ctx.fill()
            ctx.gray(0.69)
            ctx.begin_path()
            ctx.arc(0, 0, RADIUS, 0, tau, 0)
            ctx.stroke()
        else:
            ctx.begin_path()
            ctx.gray(1.0)
            utils.circle(ctx, 0, 0, RADIUS)
        
        ctx.save()
        ctx.rotate(tau / 10 + tau / 5)
        start = self.time + self.data.period * 4
        stop = self.time
        for i in range(5):
            for event in self.events:
                if not isinstance(event, midireader.Note): continue
                if not start >= event.time >= stop and not start >= (event.time + event.length) >= stop and not event.time <= stop <= (event.time + event.length): continue
                if not event.number == i: continue

                ctx.begin_path()
                time = event.time - VIDEO_DELAY

                length = event.length
                during = False
                arc = tau/20
                if event.played or (self.demo_mode and event.time <= self.time + VIDEO_DELAY <= event.time + event.length):
                    length -= self.time - event.time + VIDEO_DELAY
                    time = self.time
                    if length < 0:
                        length = 0
                    if not event.missed or self.demo_mode:
                        during = True
                        arc *= 1.5
                    
                ctx.line_width = 6
                ctx.line_cap = ctx.NONE
                if event.length > 120 or (event.missed and not self.demo_mode):
                    d = 0.75 if not event.missed or event.played else 0.33
                    if during: d = 1.0
                    ctx.rgb(*utils.dim(utils.PETAL_COLORS[i], d))
                    pos1 = max(0, - (stop - time) / (start - stop) * (120 - RADIUS) + RADIUS)
                    pos2 = max(0, - (stop - (time + length)) / (start - stop) * (120 - RADIUS) + RADIUS)
                    ctx.rectangle(-3, pos1, 6, pos2-pos1)
                    ctx.fill()
                    #ctx.move_to(0, max(0, - (stop - time) / (start - stop) * (120 - RADIUS) + RADIUS))
                    #ctx.line_to(0, max(0, - (stop - (time + length)) / (start - stop) * (120 - RADIUS) + RADIUS))
                    #ctx.stroke()
                
                ctx.rgb(*utils.PETAL_COLORS[i])
                pos = - (stop - time) / (start - stop)
                ctx.line_width = 3 + 3 * pos + during * 2
                
                if pos >= 0 and (not event.missed or self.demo_mode): # and not self.debug:
                    ctx.arc(0, 0, pos * (120 - RADIUS) + RADIUS, -arc + tau / 4, arc + tau / 4, 0)
                    #ctx.arc(0, 0, max(0, - (stop - (time + length)) / (start - stop) * 120), -tau/40, tau/40, 1)
                    ctx.stroke()

            ctx.rotate(tau / 5)
        ctx.restore()
        
        ctx.line_width = 2

        ctx.save()
        ctx.scale(0.42 + 0.05 * (self.good - self.miss), 0.42 + 0.05 * (self.good - self.miss))
        self.time += VIDEO_DELAY
        wiggle = math.cos(((self.time / self.data.period / 2) % 1) * tau) * 0.1
        self.flower.rot = tau / 5 / 2 + wiggle
        ctx.rgb(0.945, 0.631, 0.769)
        self.flower.draw(ctx)
        ctx.restore()
        
        col = 0.3 * (1.0 - ((((self.time / self.data.period) % 1)**2) * 0.75) if self.started else 0.0)
        ctx.rgb(min(1.0, col + self.bad * 0.75), col + self.bad * 0.1, col + self.bad * 0.2)
        ctx.begin_path()
        ctx.arc(0, 0, 10 * (1.0 + 0.05 * (self.good - self.miss)), 0, tau, 0)
        ctx.fill()
        self.time -= VIDEO_DELAY
        
        ctx.save()
        ctx.rgb(0.5 + self.bad * 0.4, 0.5, 0.5)
        #ctx.rotate(wiggle)
        if self.started:
            ctx.rectangle(-8, -8, 15, 15)
            ctx.clip() # for firmwares that stroke the scope...
            ctx.scale(0.0625, 0.125 * 0.3)
            ctx.begin_path()
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
        if media.get_time() * 1000 + AUDIO_DELAY == self.time:
            self.successive_sames += min(delta_ms, 100)
        else:
            self.successive_sames = 0

        #if self.input.buttons.app.middle.pressed:
        #    self.successive_sames = 1000

        if self.successive_sames > 250 and not self.finished:
            self.finished = True
            media.stop()
            self.vm.replace(score.ScoreView(self.app, self.data, self.longeststreak))

        if self.input.buttons.os.middle.pressed:
            self.vm.pop(ViewTransitionSwipeRight())

        if self.streak > self.longeststreak:
            self.longeststreak = self.streak

        self.delay -= delta_ms
        self.time += delta_ms

        if self.delay < -AUDIO_DELAY and not self.started:
            self.started = True
            if self.song:
                media.load(self.song.dirName + '/song.mp3')

        if self.song and self.started:
            self.time = media.get_time() * 1000 + AUDIO_DELAY

        if self.input.buttons.app.middle.pressed:
            self.demo_mode = not self.demo_mode

        if self.input.buttons.app.left.pressed:
            self.fps = not self.fps

        if self.input.buttons.app.right.pressed:
            self.debug = not self.debug
            
        self.good = max(0, self.good - delta_ms / self.data.period)
        self.bad = max(0, self.bad - delta_ms / 500)
        self.miss = max(0, self.miss - delta_ms / self.data.period)
        for i in range(5):
            self.missed[i] = max(0, self.missed[i] - delta_ms / 1500)

        earlyMargin       = 60000.0 / self.data.bpm / 3.5
        lateMargin        = 60000.0 / self.data.bpm / 3.5

        notes = set()
        events_in_margin = set()
        if self.app:
            self.events = self.data.track.getEvents(self.time - self.data.period / 2, self.time + self.data.period * 4)
        for event in self.events:
            if isinstance(event, midireader.Note):
                if event.time <= self.time <= event.time + event.length:
                    notes.add(event.number)
                if event.time - earlyMargin <= self.time <= event.time + lateMargin:
                    events_in_margin.add(event)
                if event.time + lateMargin < self.time and not event.played and not event.missed:
                    event.missed = True
                    self.streak = 0
                    if not self.demo_mode:
                        self.missed[event.number] = 1.0
                        self.miss = 1.0
                if event.played and event.time + event.length - lateMargin > self.time:
                    p = 4 if event.number == 0 else event.number - 1
                    if not ins.captouch.petals[p*2].pressed and not event.missed:
                        event.missed = True


        if self.exiting:
            return

        leds.set_all_rgb(0, 0, 0)

        for petal in range(5):
            p = 4 if petal == 0 else petal - 1
            pressed = ins.captouch.petals[p*2].pressed
            events = set(filter(lambda x: x.number == petal, events_in_margin))

            self.led_override[petal] = max(0, self.led_override[petal] - delta_ms)

            if self.input.captouch.petals[p*2].whole.pressed:
                if not events:
                    utils.play_fiba(self.app)
                    self.bad = 1.0
                    self.streak = 0
                else:
                    for event in events:
                        #if not event.played:
                        #    print(self.time - event.time)
                        if not event.played:
                            event.played = True
                            self.led_override[petal] = 100
                            if event.time > self.laststreak:
                                self.streak += 1
                                self.laststreak = event.time
                            self.petals[petal] = event
                    self.good = 1.0

            if not pressed:
                self.petals[petal] = None

            active = self.petals[petal] is not None
            d = 1.0 if (active and self.petals[petal].time + self.petals[petal].length >= self.time) or self.led_override[petal] else (0.15 if pressed else (1.0 if petal in notes and self.demo_mode else 0.069))
            if d:
                utils.petal_leds(petal, d)

        leds.update()

    def on_enter(self, vm: Optional[ViewManager]) -> None:
        super().on_enter(vm)
        if self.app:
            media.load(self.app.path + '/sounds/start.mp3')
            self.app.blm.volume = 10000
        for i in range(5):
            utils.petal_leds(i, 0.069)
        leds.update()
        #gc.disable()

    def on_exit(self):
        sys_display.set_mode(0)
        super().on_exit()
        self.exiting = True
        if self.app and not self.finished:
            self.app.blm.volume = 14000
            utils.play_back(self.app)
        leds.set_all_rgb(0, 0, 0)
        leds.update()
        #gc.enable()

if __name__ == '__main__':
    media.stop()
    view = SongView(None, None, None)
    view.fps = True
    st3m.run.run_view(view)
