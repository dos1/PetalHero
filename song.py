from st3m.input import InputController
from st3m.ui.view import BaseView, ViewManager, ViewTransitionSwipeLeft
from st3m.application import Application, ApplicationContext
import media

import midi
import midireader

class SongView(BaseView):
    def __init__(self, app):
        super().__init__()
        self.app = app
        midiIn = midi.MidiInFile(midireader.MidiReader(None), self.app.path + '/notes.mid')
        midiIn.read()

    def draw(self, ctx: Context) -> None:
        # Paint the background black
        ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()
        # Green square
        ctx.rgb(0, 255, 0).rectangle(-20, -20, 40, 40).fill()

    def think(self, ins: InputState, delta_ms: int) -> None:
        self.input.think(ins, delta_ms)
        media.think(delta_ms)

    def on_enter(self, vm: Optional[ViewManager]) -> None:
        super().on_enter(vm)
        #self._vm = vm
        # Ignore the button which brought us here until it is released
        #self.input._ignore_pressed()
        media.load('/sd/song.mp3')

    def on_exit(self):
        super().on_exit()
        self.app.out_sound.signals.trigger.start()
