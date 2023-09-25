from st3m.ui.view import BaseView, ViewManager, ViewTransitionSwipeRight, ViewTransitionBlend
from st3m.ui.colours import *
from st3m.utils import tau
import st3m.run
import math
import leds
import sys_display
import sys_scope
from micropython import const
from time import ticks_ms, sleep
try:
    import media
    from st3m.ui.view import ViewTransitionDirection
except ImportError:
    pass

if __name__ == '__main__':
    import sys
    sys.path.append('/flash/apps/PetalHero')

import midi
import midireader
import utils
import flower
import score
import gc

AUDIO_DELAY = const(-90)
VIDEO_DELAY = const(60 - AUDIO_DELAY)
RADIUS = const(22)
tau = const(6.283185307179586)

class SongView(BaseView):
    def __init__(self, app, song, difficulty):
        super().__init__()
        self.app = app
        self.song = song
        self.difficulty = difficulty
        if self.app:
            self.app.load_fiba()
        if self.song:
            self.data = midireader.MidiReader(self.difficulty)
            midiIn = midi.MidiInFile(self.data, self.song.dirName + '/notes.mid')
            midiIn.read()
        else:
            self.data = midireader.MidiReader(None)
            self.data.period = 500
            self.data.bpm = 120
        self.started = False
        self.time = -2000 - AUDIO_DELAY
        if self.song:
            self.time -= self.song.delay
        self.flower = flower.Flower(0)
        self.events = set()
        self.petals = [None] * 5
        self.demo_mode = False
        self.fps = False
        self.debug = False
        self.paused = False
        self.first_think = False
        self.finished = False
        self.streak = 0
        self.longeststreak = 0
        self.led_override = [0] * 5
        self.laststreak = -1
        self.notes = set()
        self.events_in_margin = set()
        self.petal_events = [set() for i in range(5)]
        self.last_played = 0
        self.last_time = 0
        
        self.good = 0.0
        self.bad = 0.0
        self.missed = [0.0] * 5
        self.miss = 0.0

        #self.oldmem = 0
        #self.redraw = True
        #self.acc = 0

    def draw(self, ctx: Context) -> None:
        #mem = gc.mem_alloc()
        #self.redraw = True
        self.time += VIDEO_DELAY
        
        other = int(self.time / 2 / self.data.period) % 2
        if self.time < 0:
            other = not other

        utils.clear(ctx, (0.1 if other else 0.0) + self.miss * 0.15)
                
        ctx.gray(0.25)
        
        i = 1
        while i >= 0:
            #ctx.gray(0.4 + i * 0.12 + (1-(self.time/2 / self.data.period) % 1) * 0.12)
            #ctx.line_width = 1.75 + i * 0.12 + (1-(self.time/2 / self.data.period) % 1) * 0.12
            ctx.gray((0.1 if other ^ (i == 1) else 0.0) + self.miss * 0.15)
            pos = (120-RADIUS)/2 * (i+1-(self.time/2 / self.data.period) % 1)
            if pos > 0:
                #ctx.begin_path()
                if self.debug and False:
                    utils.circle(ctx, 0, 0, RADIUS + pos)
                else:
                    ctx.arc(0, 0, RADIUS + pos, 0, tau, 0)
                    ctx.fill()
            i -= 1
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

        if not self.debug or True:
            ctx.gray(0.69)
            ctx.arc(0, 0, RADIUS + 1.5, 0, tau, 0)
            ctx.fill()
            for i in range(5):
                ctx.gray(math.sqrt(self.missed[i]) * 0.6)
                ctx.arc(0, 0, RADIUS - 1.5, (tau / 5) * (i - 2.25 - 0.5), (tau / 5) * (i - 2.25 + 0.5), 0)
                ctx.line_to(0, 0)
                ctx.fill()
        else:
            ctx.begin_path()
            ctx.gray(1.0)
            utils.circle(ctx, 0, 0, RADIUS)
        
        ctx.save()
        ctx.rotate(const(tau / 10 + tau / 5))
        start = self.time + self.data.period * 4
        stop = self.time
        for i in range(5):
            for event in self.events:
                if not isinstance(event, midireader.Note): continue
                if not event.number == i: continue
                if not start >= event.time >= stop and not start >= (event.time + event.length) >= stop and not event.time <= stop <= (event.time + event.length): continue
                
                chord = False
                for e in self.events:
                    if e != event and e.time == event.time:
                        chord = True
                        break

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
                        arc *= 1.66
                    
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
                
                pos = - (stop - time) / (start - stop)
                ctx.line_width = 3 + 3 * pos + during * 2
                
                if pos >= 0 and (not event.missed or self.demo_mode): # and not self.debug:
                    if chord:
                        ctx.gray(0.8)
                        ctx.arc(0, 0, pos * (120 - RADIUS) + RADIUS, -(arc*1.25) + tau / 4, -arc + tau / 4, 0)
                        ctx.stroke()
                        ctx.arc(0, 0, pos * (120 - RADIUS) + RADIUS, arc + tau / 4, (arc*1.25) + tau / 4, 0)
                        ctx.stroke()
                    ctx.rgb(*utils.PETAL_COLORS[i])
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
        #ctx.rectangle(-8, -8, 15, 15)
        #ctx.clip()
        ctx.line_width = 12
        ctx.scale(0.0625, 0.125 * 0.3)
        #ctx.rotate(wiggle)
        ctx.begin_path()
        if self.started:
            buf = sys_scope.get_buffer_x()
            ctx.move_to(-120, 0)
            for i in range(0, len(buf), 32):
                val = buf[i] / 32
                ctx.line_to(-120 + i, max(6, val))
            for i in range(len(buf) - 1, 0, -32):
                val = buf[i] / 32
                ctx.line_to(-120 + i, min(-6, val))
            ctx.fill()
        else:
            ctx.move_to(-120, 0)
            ctx.line_to(120, 0)
            ctx.stroke()
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
            
        if self.paused:
            ctx.rgba(0, 0, 0, 0.5)
            ctx.rectangle(-120, -120, 240, 240).fill()
            ctx.move_to(0, 0)
            ctx.gray(0.9)
            ctx.font = "Camp Font 2"
            ctx.font_size = 64
            ctx.text("PAUSED")
        #print("draw", gc.mem_alloc() - mem)
        #t = ticks_ms()
        #print(ticks_ms() - t)
        
        #gc.collect()
        #sleep(0.2)

    def think(self, ins: InputState, delta_ms: int) -> None:
        #mem = gc.mem_alloc()
        #print(mem - self.oldmem)
        #self.oldmem = mem

        #self.acc += delta_ms
        #if self.redraw:
        #    delta_ms = self.acc
        #    self.acc = 0
        #    self.redraw = False
        #else:
        #    return
        #if (delta_ms > 100): print(delta_ms)
        
        super().think(ins, delta_ms)
        utils.blm_timeout(self, delta_ms)

        if self.first_think:
            self.first_think = False
            return

        media.think(delta_ms)

        if self.input.buttons.os.middle.pressed and not self.is_active(): # TODO: will that work with pending transitions?
            self.vm.push(self)
            self.vm.pop(ViewTransitionSwipeRight(), depth=2)
            return

        if not self.is_active():
            return

        if self.song and self.started and media.get_position() == media.get_duration() and not self.finished:
            self.finished = True
            media.stop()
            gc.collect()
            self.vm.replace(score.ScoreView(self.app, self.data, self.longeststreak), ViewTransitionBlend())
            return

        if self.streak > self.longeststreak:
            self.longeststreak = self.streak

        if not self.paused:
            self.time += delta_ms

        delay = AUDIO_DELAY
        if self.song:
             delay -= self.song.delay
        if self.time >= delay and not self.started:
            self.started = True
            if self.song:
                media.load(self.song.dirName + '/song.mp3')

        if self.song and self.started:
            self.time = media.get_time() * 1000 + delay

        if self.input.buttons.app.middle.pressed:
            if self.paused:
                media.play()
            else:
                media.pause()
            self.paused = not self.paused

        if self.input.buttons.app.left.pressed:
            self.fps = not self.fps
            self.debug = not self.debug

        if self.input.buttons.app.right.pressed:
            self.demo_mode = not self.demo_mode
            if self.demo_mode:
                media.set_volume(1.0)

        if self.paused:
            return
        
        delta_time = self.time - self.last_time
        delta_ms = min(delta_ms, 100)

        self.good = max(0, self.good - delta_ms / self.data.period)
        self.bad = max(0, self.bad - delta_ms / 500)
        self.miss = max(0, self.miss - delta_ms / self.data.period)
        for i in range(5):
            self.missed[i] = max(0, self.missed[i] - delta_ms / 1500)
            self.petal_events[i].clear()

        earlyMargin       = 60000.0 / self.data.bpm / 3.5
        lateMargin        = 60000.0 / self.data.bpm / 3.5 + delta_time

        self.notes.clear()
        self.events_in_margin.clear()

        if self.app and not self.finished:
            self.data.track.getEvents(self.time - self.data.period / 2, self.time + self.data.period * 4, self.events)
        else:
            self.events.clear()
        
        for event in self.events:
            if event.time <= self.time <= event.time + event.length:
                self.notes.add(event.number)
            if self.time - lateMargin <= event.time <= self.time + earlyMargin:
                self.events_in_margin.add(event)
                if not event.played:
                    self.petal_events[event.number].add(event)
            if event.time + lateMargin < self.time and not event.played and not event.missed:
                event.missed = True
                self.streak = 0
                if not self.demo_mode:
                    self.missed[event.number] = 1.0
                    self.miss = 1.0
                    if event.time >= self.last_played and not self.demo_mode:
                        media.set_volume(0.25)
            if event.played and min(event.time + event.length - lateMargin * 2, event.time + 0.66 * event.length) > self.time:
                p = 4 if event.number == 0 else event.number - 1
                if not ins.captouch.petals[p*2].pressed and not event.missed:
                    event.missed = True
                    media.set_volume(0.25)

        leds.set_all_rgb(0, 0, 0)

        for petal in range(5):
            p = 4 if petal == 0 else petal - 1
            pressed = ins.captouch.petals[p*2].pressed
            events = self.petal_events[petal]

            self.led_override[petal] = max(0, self.led_override[petal] - delta_ms)

            if self.input.captouch.petals[p*2].whole.pressed:
                if not events:
                    utils.play_fiba(self.app)
                    self.bad = 1.0
                    self.streak = 0
                else:
                    event = min(events, key=lambda x: abs(self.time - x.time))
                    
                    # is it part of a chord with already released notes?
                    bad_chord = False
                    for e in self.events_in_margin:
                        if e != event and e.time == event.time and e.missed:
                            bad_chord = True
                            break
                        
                    if bad_chord:
                        utils.play_fiba(self.app)
                        self.bad = 1.0
                        self.streak = 0
                    else:
                        event.played = True
                        
                        if event.time > self.laststreak:
                            self.streak += 1
                            self.laststreak = event.time
                            if self.debug:
                                print(self.time - event.time)

                        self.laststreak = event.time
                        self.led_override[petal] = 50
                        self.petals[petal] = event
                        self.good = 1.0
                        self.last_played = event.time
                        media.set_volume(1.0)

            if not pressed:
                self.petals[petal] = None

            active = self.petals[petal] is not None
            d = 1.0 if (active and self.petals[petal].time + self.petals[petal].length >= self.time) or self.led_override[petal] else (0.15 if pressed else (1.0 if petal in self.notes and self.demo_mode else 0.069))
            if d:
                utils.petal_leds(petal, d)

        # if there were several events in-between think calls, we have no idea
        # whether they were played correctly or not. let's be generous to the
        # player and assume they were
        now = max(self.last_played, self.time)
        for event in self.events_in_margin:
            p = 4 if event.number == 0 else event.number - 1
            if not self.petals[p] or event.time >= self.petals[p].time: continue
            if event.played or event.time >= now or event.time < now - delta_time: continue
            event.played = True
            # mark chords as played too already so we only count streak once
            for e in self.events_in_margin:
                if not event.played and e.time == event.time:
                    e.played = True
            self.streak += 1

        leds.update()
        #gc.collect()
        #print("think", gc.mem_alloc() - mem)
        
        self.last_time = self.time

    def on_enter(self, vm: Optional[ViewManager]) -> None:
        super().on_enter(vm)
        self.first_think = True
        if self.vm.direction == ViewTransitionDirection.FORWARD: # self-pushed
            return
        if self.app:
            media.load(self.app.path + '/sounds/start.mp3')
            utils.volume(self.app, 8000)
        leds.set_slew_rate(238)
            
    def on_enter_done(self):
        #sys_display.set_mode(sys_display.get_mode() | 512)
        for i in range(5):
            utils.petal_leds(i, 0.069)
        leds.update()
        #gc.disable()

    def on_exit(self):
        super().on_exit()
        #sys_display.set_mode(sys_display.get_mode() & ~512)
        leds.set_all_rgb(0, 0, 0)
        leds.update()
        #gc.enable()

        if self.app and not self.finished:
            utils.volume(self.app, 14000)
            utils.play_back(self.app)
            
        if self.song and not self.started:
            media.load(self.song.dirName + '/song.mp3')

if __name__ == '__main__':
    media.stop()
    view = SongView(None, None, None)
    view.fps = True
    st3m.run.run_view(view)
