from st3m.input import InputController
from st3m.ui.view import BaseView, ViewManager, ViewTransitionSwipeRight
from st3m.application import Application, ApplicationContext
from st3m.ui.colours import *
import media
import leds

import midi
import midireader

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
        self.time = 0

    def draw(self, ctx: Context) -> None:
        # Paint the background black
        ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()
        # Green square
        ctx.rgb(0, 255, 0).rectangle(-20, -20, 40, 40).fill()
        
        ctx.move_to(0, 40)
        ctx.gray(1.0)
        
        #for time, event in self.data.tracks[self.difficulty.id].getEvents(self.time - self.data.period * 2, self.time + self.data.period * 4):
        #    print(event)
        a = ""
        earlyMargin       = 60000.0 / self.data.bpm / 3.5
        lateMargin        = 60000.0 / self.data.bpm / 3.5

        notes = set()
        for time, event in self.data.tracks[self.difficulty.id].getEvents(self.time - 50, self.time):
            if isinstance(event, midireader.Note):
                notes.add(event.number)
                
        for note in notes:
            a += str(note)
        ctx.text(a)
        
        leds.set_all_rgb(0, 0, 0)
        led = -11
        petal = 0
        for col in [GO_GREEN, RED, (1.0, 0.69, 0.0), BLUE, PUSH_RED]:
            for i in range(7):
                if petal in notes:
                    leds.set_rgb(led if led >= 0 else led + 40, *col)
                led += 1
            leds.set_rgb(led, 0, 0, 0)
            led += 1
            petal += 1
            
        leds.update()
                

    def think(self, ins: InputState, delta_ms: int) -> None:
        self.input.think(ins, delta_ms)
        media.think(delta_ms)
        if self.input.buttons.os.middle.pressed:
            self.vm.pop(ViewTransitionSwipeRight())
        self.delay -= delta_ms
        #if delta_ms < 100:
        self.time += delta_ms
        if self.delay < 0 and not self.started:
            self.started = True
            media.load(self.song.dirName + '/song.mp3')
            self.time = 0

    def on_enter(self, vm: Optional[ViewManager]) -> None:
        super().on_enter(vm)
        #self._vm = vm
        # Ignore the button which brought us here until it is released
        #self.input._ignore_pressed()
        media.load(self.app.path + '/start.mp3')

    def on_exit(self):
        super().on_exit()
        self.app.out_sound.signals.trigger.start()
