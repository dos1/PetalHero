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

AUDIO_STARTUP = const(750) # how early should audio be loaded
VIDEO_DELAY = const(80) # delay between audio and what's displayed on the screen
INPUT_DELAY = const(20) # additional headroom for input handling
DELTA_THRESHOLD = const(60) # above this we assume that there may be missed release events
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
            self.data.bpm = 120
            self.data.period = 60000.0 / self.data.bpm
            self.data.tempoMarkers = [(0, self.data.bpm)]
        self.started = False
        self.loaded = False
        self.time = -max(1800 + AUDIO_STARTUP, self.data.period * 4)
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
        self.last_played = None
        self.last_played_petal = [None] * 5
        self.last_time = 0
        self.last_state = [False] * 5
        
        self.good = 0.0
        self.bad = 0.0
        self.missed = [0.0] * 5
        self.bads = [0.0] * 5
        self.miss = 0.0

        #self.oldmem = 0
        #self.redraw = True
        #self.acc = 0
        
        self.beat_point = 0
        self.tempo_mark = 0
        self.bpm = self.data.bpm
        self.period = self.data.period
        self.beat = 0
        self.beats = []
        
        if self.data.beats:
            self.mid_period = sum(map(lambda x: x[1]-x[0], zip(self.data.beats ,self.data.beats[1:]))) / (len(self.data.beats) - 1)
            self.mid_bpm = 60000.0 / self.mid_period
        else:
            self.mid_bpm = (max(self.data.tempoMarkers, key=lambda x: x[1])[1] + min(self.data.tempoMarkers, key=lambda x: x[1])[1]) / 2
            self.mid_period = 60000.0 / self.mid_bpm

        self.current_beat = 0

    def _next_beat_at(self, time):
        # won't return anything earlier than current beat

        if time < self.time + VIDEO_DELAY - 1:
            diff = self.time + VIDEO_DELAY - time
            if diff > (self.beat - int(self.beat)) * self.period + 1:
                return (self.time + VIDEO_DELAY - self.period * (self.beat - int(self.beat)), int(self.beat))
        
        if self.data.beats:
            beat = self.current_beat
            while len(self.data.beats) > beat and time + VIDEO_DELAY >= self.data.beats[beat]:
                beat += 1
            if len(self.data.beats) > beat and time < self.data.beats[beat]:
                return (self.data.beats[beat], beat)
        
        beat_point = self.beat_point
        period = self.period
        tempo_mark = self.tempo_mark

        cur_beat = beat_point + (time - self.data.tempoMarkers[tempo_mark][0]) / period
        next_beat_at = time + period * (1.0 - cur_beat % 1)
        
        while len(self.data.tempoMarkers) > tempo_mark + 1 and next_beat_at > self.data.tempoMarkers[tempo_mark + 1][0]:
            next_beat_at -= period
            beat_point += (self.data.tempoMarkers[tempo_mark + 1][0] - self.data.tempoMarkers[tempo_mark][0]) / period
            tempo_mark += 1
            period = 60000.0 / self.data.tempoMarkers[tempo_mark][1]
            cur_beat = beat_point + (time - self.data.tempoMarkers[tempo_mark][0]) / period
            next_beat_at = time + period * (1.0 - cur_beat % 1)

        if next_beat_at - time < 1:
            return self._next_beat_at(next_beat_at + 1)

        return next_beat_at, int(cur_beat) + 1


    def draw(self, ctx: Context) -> None:
        #mem = gc.mem_alloc()
        #self.redraw = True        
        start = self.time - INPUT_DELAY + self.mid_period * 4
        start_marg = start + self.mid_period * 0.25
        stop = self.time - INPUT_DELAY

        beat_no = self.beats[-1][1]
        #if beat_no <= 0:
        #    beat_no -= 2
        other = int((beat_no / 2) % 2)
        utils.clear(ctx, (0.1 if other else 0.0) + self.miss * 0.15)
                
        ctx.gray(0.25)
        
        for i in range(len(self.beats)):
            t, no = self.beats[len(self.beats) - i - 1]
            t -= VIDEO_DELAY - INPUT_DELAY
            #if no <= 0:
            #    no -= 2
            if int(no) % 2:
                continue
            #ctx.gray(0.4 + i * 0.12 + (1-(self.time/2 / self.data.period) % 1) * 0.12)
            #ctx.line_width = 1.75 + i * 0.12 + (1-(self.time/2 / self.data.period) % 1) * 0.12
            ctx.gray((0.1 * ((int((abs(no) + 1) / 2) % 2) == 0)) + self.miss * 0.15)
            pos = (120-RADIUS) * ((t - stop) / (start - stop))
            if pos > 0:
                #ctx.begin_path()
                if self.debug and False:
                    utils.circle(ctx, 0, 0, RADIUS + pos)
                else:
                    ctx.arc(0, 0, RADIUS + pos, 0, tau, 0)
                    ctx.fill()
        
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
        for i in range(5):
            for event in self.events:
                if not event.number == i: continue
                if self.petals[event.number] != event or self.led_override[event.number] == 0:
                    if not start_marg >= event.time >= stop and not start_marg >= (event.time + event.length) >= stop and not event.time <= stop <= (event.time + event.length):
                        continue
                
                chord = False
                for e in self.events:
                    if e != event and e.time == event.time:
                        chord = True
                        break

                ctx.begin_path()
                time = event.time - VIDEO_DELAY + INPUT_DELAY

                length = event.length
                during = False
                arc = tau/20
                if event.played or (self.demo_mode and event.time <= self.time + VIDEO_DELAY - INPUT_DELAY <= event.time + event.length):
                    length -= self.time - event.time + VIDEO_DELAY - INPUT_DELAY
                    time = self.time - INPUT_DELAY
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
        wiggle = math.cos(((self.beat / 2) % 1) * tau) * 0.1
        self.flower.rot = tau / 5 / 2 + wiggle
        ctx.rgb(0.945, 0.631, 0.769)
        self.flower.draw(ctx)
        ctx.restore()
        
        col = 0.3 * (1.0 - ((((self.beat) % 1)**2) * 0.75))
        ctx.rgb(min(1.0, col + self.bad * 0.75), col + self.bad * 0.1, col + self.bad * 0.2)
        ctx.begin_path()
        ctx.arc(0, 0, 10 * (1.0 + 0.05 * (self.good - self.miss)), 0, tau, 0)
        ctx.fill()
        
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
        
        ctx.save()
        ctx.rotate(tau / 10 + tau / 5)
        for petal in range(5):
            ctx.line_width = 2
            arc = tau/10
            if self.bads[petal]:
                ctx.rgba(*utils.dim(utils.PETAL_COLORS[petal], 0.9), self.bads[petal])
                ctx.arc(0, 0, 10 * (1.0 + 0.05 * (self.good - self.miss)) - 1, -arc + tau / 4, arc + tau / 4, 0)
                ctx.stroke()
            ctx.rotate(tau / 5)
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
        #sleep(0.25)

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

        if not self.first_think:
            media.think(delta_ms)

        if self.input.buttons.os.middle.pressed and not self.is_active():
            while not self.vm.is_active(self.app):
                self.vm.pop(ViewTransitionSwipeRight())

        if not self.is_active():
            return

        if self.song and self.started and media.get_position() == media.get_duration() and not self.finished:
            self.finished = True
            media.stop()
            gc.collect()
            self.vm.replace(score.ScoreView(self.app, self.data, self.longeststreak, self.difficulty), ViewTransitionBlend())
            return

        if self.streak > self.longeststreak:
            self.longeststreak = self.streak

        if not self.paused and not self.first_think:
            self.time += delta_ms

        if self.song and self.time >= -AUDIO_STARTUP - self.song.delay and not self.loaded:
            self.loaded = True
            media.load(self.song.dirName + '/song.mp3', True)
            
        if self.song and self.song.loaded and self.time >= -self.song.delay and not self.started:
            self.started = True
            media.play()

        if self.song and self.started:
            t = media.get_time()
            if t > 0:
                self.time = media.get_time() * 1000 - self.song.delay

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

        if self.data.beats and len(self.data.beats) > self.current_beat + 1:
            while self.time + VIDEO_DELAY >= self.data.beats[self.current_beat + 1]:
                if self.current_beat == len(self.data.beats) - 2:
                    break
                self.current_beat += 1

        if len(self.data.tempoMarkers) > self.tempo_mark + 1:
            time, bpm = self.data.tempoMarkers[self.tempo_mark]
            new_time, new_bpm = self.data.tempoMarkers[self.tempo_mark + 1]
            while self.time + VIDEO_DELAY >= new_time:
                self.beat_point += (new_time - time) / (60000.0 / bpm)
                if self.data.beats and len(self.data.beats) > self.current_beat + 1:
                    self.beat_point = self.current_beat + (new_time - self.data.beats[self.current_beat]) / (self.data.beats[self.current_beat + 1] - self.data.beats[self.current_beat])
                self.bpm = new_bpm
                self.period = 60000.0 / self.bpm
                self.tempo_mark += 1
                time, bpm = self.data.tempoMarkers[self.tempo_mark]
                if self.tempo_mark + 1 == len(self.data.tempoMarkers):
                    break
                new_time, new_bpm = self.data.tempoMarkers[self.tempo_mark + 1]

        if self.data.beats and len(self.data.beats) > self.current_beat + 1:
            self.period = self.data.beats[self.current_beat + 1] - self.data.beats[self.current_beat]
            self.bpm = 60000.0 / self.period
            self.beat = self.current_beat + (self.time + VIDEO_DELAY - self.data.beats[self.current_beat]) / (self.data.beats[self.current_beat + 1] - self.data.beats[self.current_beat])
            #if self.debug and not self.paused:
            #    print(self.time + VIDEO_DELAY, self.beat, self.current_beat, self.data.beats[self.current_beat], self.data.beats[self.current_beat + 1], len(self.data.beats))
        else:
            self.beat = self.beat_point + (self.time + VIDEO_DELAY - self.data.tempoMarkers[self.tempo_mark][0]) / self.period
            #if self.debug and not self.paused and len(self.data.tempoMarkers) > 1:
            #    print(self.time + VIDEO_DELAY, self.beat, self.beat_point, self.tempo_mark, self.data.tempoMarkers[self.tempo_mark], self.data.tempoMarkers[self.tempo_mark + 1])

        self.beats.clear()
        start = self.time + VIDEO_DELAY - INPUT_DELAY
        stop = self.time + VIDEO_DELAY - INPUT_DELAY + self.mid_period * 4
        if start < 0:
            for i in range(-12, 0):
                if len(self.data.beats) > 1:
                    a = (self.data.beats[1] - self.data.beats[0]) * i
                else:
                    a = self.data.period * i
                if a > start and a < stop:
                    self.beats.append((a, i))
            if 0 < stop:
                self.beats.append((0, 0))
        t = max(0, start)
        t, no = self._next_beat_at(t)
        while t < stop:
            self.beats.append((t, no))
            t, no = self._next_beat_at(t)
        #if self.debug and not self.paused:
        #    print(self.time + VIDEO_DELAY - INPUT_DELAY, self.beat, self.bpm, self.period, self.beats)

        if self.paused:
            return
        
        delta_time = self.time - self.last_time
        delta_ms = min(delta_ms, 100)

        self.good = max(0, self.good - delta_ms / self.period)
        self.bad = max(0, self.bad - delta_ms / 500)
        self.miss = max(0, self.miss - delta_ms / self.period)
        for i in range(5):
            self.missed[i] = max(0, self.missed[i] - delta_ms / 1500)
            self.bads[i] = max(0, self.bads[i] - delta_ms / 750)
            self.petal_events[i].clear()

        earlyMargin       = 60000.0 / max(100, min(self.bpm, 200)) / 3.5 * 0.5
        lateMargin        = 60000.0 / max(100, min(self.bpm, 200)) / 3.5 + INPUT_DELAY

        self.notes.clear()
        self.events_in_margin.clear()

        if self.app and not self.finished:
            self.data.track.getEvents(self.time - self.mid_period / 2, self.time + self.mid_period * 4.5, self.events)
        else:
            self.events.clear()

        for event in self.events:
            if event.time <= self.time <= event.time + event.length:
                self.notes.add(event.number)
            if self.time - lateMargin - delta_time <= event.time <= self.time + earlyMargin:
                self.events_in_margin.add(event)
                if (not event.played and not event.missed) or event.ghost:
                    self.petal_events[event.number].add(event)
            if event.ghost and event.time + lateMargin + delta_time < self.time:
                event.ghost = False
            if event.time + lateMargin + delta_time < self.time and not event.played and not event.missed:
                event.missed = True
                #print("MISSED", event, self.time, delta_time)
                self.streak = 0
                for e in self.events:
                    if e.time == event.time:
                        e.missed = True
                        if self.petals[e.number] == e:
                            self.petals[e.number] = None
                        
                if not self.demo_mode:
                    self.missed[event.number] = 1.0
                    self.miss = 1.0
                    if event.time >= (self.last_played.time if self.last_played else 0) and not self.demo_mode:
                        media.set_volume(0.25)
            if event.played and not event.ghost and min(event.time + event.length - lateMargin * 2, event.time + 0.66 * event.length) > self.time:
                p = 4 if event.number == 0 else event.number - 1
                if not ins.captouch.petals[p*2].pressed and not event.missed and not event.ghost:
                    event.missed = True
                    media.set_volume(0.25)

        leds.set_all_rgb(0, 0, 0)

        played_events = set()
        ghost_events = set()
        for petal in range(5):
            p = 4 if petal == 0 else petal - 1
            pressed = ins.captouch.petals[p*2].pressed
            events = self.petal_events[petal]

            self.led_override[petal] = max(0, self.led_override[petal] - delta_ms)

            # we can't rely on release events being delivered if delta_time gets high
            # TODO: revisit once the new input API is there
            if self.input.captouch.petals[p*2].whole.pressed or (delta_time >= DELTA_THRESHOLD and pressed):
                #if delta_time >= DELTA_THRESHOLD: print("delta", delta_time)
                if not events:
                    if delta_time < DELTA_THRESHOLD and not self.last_state[petal]:
                        #print("fiba", petal, self.time, delta_time)
                        utils.play_fiba(self.app)
                        self.bad = 1.0
                        self.bads[petal] = 1.0
                        self.streak = 0
                else:
                    event = min(events, key=lambda x: x.time)
                    # mark the first event in the margin as played, and the rest within 3 times delta_time
                    # (to compensate for lost release events) as ghost notes (played, but playable again)
                    # TODO: revisit once input API offers the number of touch events that happened between ticks
                    for e in events:
                        if e != event and not e.played and abs(e.time - event.time) <= max(delta_time, 15) * 3:
                            played_events.add(e)
                            e.ghost = True
                    event.ghost = not self.input.captouch.petals[p*2].whole.pressed
                    played_events.add(event)
                                    
        for event in sorted(played_events, key=lambda x: x.time):
            # is it part of a chord with already released notes?
            bad_chord = False
            for e in self.events_in_margin:
                if e != event and e.time == event.time and e.missed:
                    bad_chord = True
                
            if bad_chord:
                utils.play_fiba(self.app)
                self.bad = 1.0
                self.bads[event.number] = 1.0
                self.streak = 0
            else:
                event.played = True
                
                if event.time > self.laststreak:
                    self.streak += 1
                    self.laststreak = event.time
                    if self.debug:
                        print(self.time - event.time, delta_time)

                self.led_override[event.number] = 50
                self.petals[event.number] = event
                self.good = 1.0
                self.last_played = event
                self.last_played_petal[event.number] = event
                media.set_volume(1.0)

        for petal in range(5):
            p = 4 if petal == 0 else petal - 1
            pressed = ins.captouch.petals[p*2].pressed
            if not pressed:
                self.petals[petal] = None

            active = self.petals[petal] is not None
            d = 1.0 if (active and self.petals[petal].time + self.petals[petal].length >= self.time) or self.led_override[petal] else (0.15 if pressed else (1.0 if petal in self.notes and self.demo_mode else 0.069))
            if d:
                utils.petal_leds(petal, d)

            self.last_state[petal] = pressed

        leds.update()
        #gc.collect()
        #print("think", gc.mem_alloc() - mem)
        
        self.last_time = self.time
        self.first_think = False

    def on_enter(self, vm: Optional[ViewManager]) -> None:
        super().on_enter(vm)
        self.first_think = True
        media.set_volume(1.0)
        if self.app:
            media.load(self.app.path + '/sounds/start.mp3')
            utils.volume(self.app, 8000)
        leds.set_slew_rate(238)
            
    def on_enter_done(self):
        #sys_display.set_mode(sys_display.get_mode() | sys_display.low_latency)
        for i in range(5):
            utils.petal_leds(i, 0.069)
        leds.update()
        #gc.disable()

    def on_exit(self):
        super().on_exit()
        #sys_display.set_mode(sys_display.get_mode() & ~sys_display.low_latency)
        leds.set_all_rgb(0, 0, 0)
        leds.update()
        #gc.enable()

        if self.app and not self.finished:
            utils.volume(self.app, 14000)
            utils.play_back(self.app)
            
        #if self.song and not self.started:
        #    media.load(self.song.dirName + '/song.mp3')

if __name__ == '__main__':
    media.stop()
    view = SongView(None, None, None)
    view.fps = True
    st3m.run.run_view(view)
