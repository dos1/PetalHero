from st3m.input import InputController
from st3m.ui.view import BaseView, ViewManager, ViewTransitionSwipeRight
from st3m.application import Application, ApplicationContext
from st3m.ui.colours import *
from st3m.utils import tau
import math
import media
import leds
import sys_display

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
        self.data = midireader.MidiReader(self.song)
        midiIn = midi.MidiInFile(self.data, self.song.dirName + '/notes.mid')
        midiIn.read()
        self.delay = 2000
        self.started = False
        self.time = -self.delay
        self.flower = flower.Flower(0)
        self.events = []

    def draw(self, ctx: Context) -> None:
        # Paint the background black
        if self.started:
            sys_display.set_mode(2)

        ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()
                
        ctx.gray(0.25)
        
        for i in range(4):
            ctx.arc(0, 0, 30 * (i+1-(self.time / self.data.period) % 1), 0, tau, 0)
            ctx.stroke()
        
        ctx.gray(0.5)
        
        ctx.save()
        ctx.rotate(tau / 5 / 2)
        for i in range(5):
            ctx.move_to(0, 0)
            ctx.line_to(0, -120)
            ctx.stroke()
            ctx.rotate(tau / 5)
        ctx.restore()
        
        ctx.save()
        ctx.rotate(tau / 10 + tau / 5)
        start = self.time + self.data.period * 4
        stop = self.time
        for i in range(5):
            ctx.rgb(*utils.PETAL_COLORS[i])
            for time, event in self.events:
                if not isinstance(event, midireader.Note): continue
                if not start >= time >= stop and not start >= (time + event.length) >= stop and not time <= stop <= (time + event.length): continue
                if not event.number == i: continue
                ctx.move_to(0, max(0, - (stop - time) / (start - stop) * 120))
                ctx.line_to(0, max(0, - (stop - (time + event.length)) / (start - stop) * 120))
                ctx.stroke()
            ctx.rotate(tau / 5)
        ctx.restore()
        
        ctx.save()
        ctx.scale(0.42, 0.42)
        wiggle = math.cos(((self.time / self.data.period / 4) % 1) * tau) * 0.1
        self.flower.rot = tau / 5 / 2 + wiggle
        self.flower.draw(ctx)
        ctx.restore()
        
        ctx.gray(0.3 * (1.0 - ((((self.time / self.data.period) % 1)**2) * 0.75) if self.started else 0.0))
        ctx.arc(0, 0, 10, 0, tau, 0)
        ctx.fill()
        
        ctx.save()
        ctx.gray(0.5)
        ctx.rectangle(-10, -10, 20, 20)
        ctx.clip()
        ctx.scale(0.125, 0.125 * 0.5)
        ctx.rotate(wiggle)
        if self.started:
            ctx.scope()
            #ctx.line_to(10, -10)
            #ctx.line_to(-10, -10)
            #ctx.line_to(-10, 0)
            ctx.line_to(120, 0)
            ctx.line_to(-120, 0)
            ctx.fill()
        ctx.restore()

    def think(self, ins: InputState, delta_ms: int) -> None:
        self.input.think(ins, delta_ms)
        media.think(delta_ms)
        if self.input.buttons.os.middle.pressed:
            self.vm.pop(ViewTransitionSwipeRight())
        self.delay -= delta_ms
        if delta_ms > 80:
            delta_ms = 60
        #if self.started:
        self.time += delta_ms
        if self.delay < 0 and not self.started:
            self.started = True
            media.load(self.song.dirName + '/song.mp3')
            #self.time = 0

        earlyMargin       = 60000.0 / self.data.bpm / 3.5
        lateMargin        = 60000.0 / self.data.bpm / 3.5

        notes = set()
        self.events = self.data.tracks[self.difficulty.id].getEvents(self.time - self.data.period * 2, self.time + self.data.period * 4)
        for time, event in self.events:
            if isinstance(event, midireader.Note):
                if time <= self.time <= time + event.length:
                    notes.add(event.number)

        if not self.started:
            return

        leds.set_all_rgb(0, 0, 0)

        for petal in notes:
            utils.petal_leds(petal, 1.0)

        leds.update()


    def on_enter(self, vm: Optional[ViewManager]) -> None:
        super().on_enter(vm)
        #self._vm = vm
        # Ignore the button which brought us here until it is released
        #self.input._ignore_pressed()
        media.load(self.app.path + '/start.mp3')

    def on_exit(self):
        sys_display.set_mode(0)
        super().on_exit()
        self.app.out_sound.signals.trigger.start()
