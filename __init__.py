import sys
import media, math, random
from st3m.ui.colours import *
from st3m.input import InputController
from st3m.ui.view import BaseView, ViewManager, ViewTransitionSwipeLeft
import leds

sys.path.append('/flash/apps/PetalHero')

import midi

AMAZING_DIFFICULTY      = 0
MEDIUM_DIFFICULTY       = 1
EASY_DIFFICULTY         = 2
SUPAEASY_DIFFICULTY     = 3

noteMap = {     # difficulty, note
  0x60: (AMAZING_DIFFICULTY,  0),
  0x61: (AMAZING_DIFFICULTY,  1),
  0x62: (AMAZING_DIFFICULTY,  2),
  0x63: (AMAZING_DIFFICULTY,  3),
  0x64: (AMAZING_DIFFICULTY,  4),
  0x54: (MEDIUM_DIFFICULTY,   0),
  0x55: (MEDIUM_DIFFICULTY,   1),
  0x56: (MEDIUM_DIFFICULTY,   2),
  0x57: (MEDIUM_DIFFICULTY,   3),
  0x58: (MEDIUM_DIFFICULTY,   4),
  0x48: (EASY_DIFFICULTY,     0),
  0x49: (EASY_DIFFICULTY,     1),
  0x4a: (EASY_DIFFICULTY,     2),
  0x4b: (EASY_DIFFICULTY,     3),
  0x4c: (EASY_DIFFICULTY,     4),
  0x3c: (SUPAEASY_DIFFICULTY, 0),
  0x3d: (SUPAEASY_DIFFICULTY, 1),
  0x3e: (SUPAEASY_DIFFICULTY, 2),
  0x3f: (SUPAEASY_DIFFICULTY, 3),
  0x40: (SUPAEASY_DIFFICULTY, 4),
}

reverseNoteMap = dict([(v, k) for k, v in list(noteMap.items())])

dim = lambda x, y: tuple(map(lambda x: x * y, x))

class Event:
  def __init__(self, length):
    self.length = length

class Note(Event):
  def __init__(self, number, length, special = False, tappable = False):
    Event.__init__(self, length)
    self.number   = number
    self.played   = False
    self.special  = special
    self.tappable = tappable
    
  def __repr__(self):
    return "Note <#%d> length %d" % (self.number, self.length)

class Tempo(Event):
  def __init__(self, bpm):
    super().__init__(0)
    self.bpm = bpm
    
  def __repr__(self):
    return "<%d bpm>" % self.bpm


class MidiReader(midi.MidiOutStream.MidiOutStream):
  def __init__(self, song):
    super().__init__()
    self.song = song
    self.bpm = 0
    self.heldNotes = {}
    self.velocity  = {}
    self.ticksPerBeat = 480
    self.tempoMarkers = []

  def addEvent(self, track, event, time = None):
    if time is None:
      time = self.abs_time()
    assert time >= 0
    #print('addEvent', track, event, time)
    #if track is None:
    #  for t in self.song.tracks:
    #    t.addEvent(time, event)
    #elif track < len(self.song.tracks):
    #  self.song.tracks[track].addEvent(time, event)

  def abs_time(self):
    def ticksToBeats(ticks, bpm):
      return (60000.0 * ticks) / (bpm * self.ticksPerBeat)

    if self.bpm:
      currentTime = midi.MidiOutStream.MidiOutStream.abs_time(self)

      # Find out the current scaled time.
      # Yeah, this is reeally slow, but fast enough :)
      scaledTime      = 0.0
      tempoMarkerTime = 0.0
      currentBpm      = self.bpm
      for i, marker in enumerate(self.tempoMarkers):
        time, bpm = marker
        if time > currentTime:
          break
        scaledTime += ticksToBeats(time - tempoMarkerTime, currentBpm)
        tempoMarkerTime, currentBpm = time, bpm
      return scaledTime + ticksToBeats(currentTime - tempoMarkerTime, currentBpm)
    return 0.0

  def header(self, format, nTracks, division):
    self.ticksPerBeat = division
    
  def tempo(self, value):
    bpm = 60.0 * 10.0**6 / value
    self.tempoMarkers.append((midi.MidiOutStream.MidiOutStream.abs_time(self), bpm))
    if not self.bpm:
      self.bpm = bpm
      #self.song.setBpm(bpm)
    #print('bpm', bpm)
    self.addEvent(None, Tempo(bpm))

  def note_on(self, channel, note, velocity):
    if self.get_current_track() > 1: return
    self.velocity[note] = velocity
    self.heldNotes[(self.get_current_track(), channel, note)] = self.abs_time()

  def note_off(self, channel, note, velocity):
    if self.get_current_track() > 1: return
    try:
      startTime = self.heldNotes[(self.get_current_track(), channel, note)]
      endTime   = self.abs_time()
      del self.heldNotes[(self.get_current_track(), channel, note)]
      if note in noteMap:
        track, number = noteMap[note]
        self.addEvent(track, Note(number, endTime - startTime, special = self.velocity[note] == 127), time = startTime)
      else:
        print("MIDI note 0x%x at %d does not map to any game note." % (note, self.abs_time()))
        pass
    except KeyError:
      print("MIDI note 0x%x on channel %d ending at %d was never started." % (note, channel, self.abs_time()))


from st3m.application import Application, ApplicationContext
import st3m.run
import leds


class Flower:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.rot = 0.0
        self.rot_speed = 1 / 800 #(((random.getrandbits(16) - 32767) / 32767.0) - 0.5) / 800

    def draw(self, ctx: Context) -> None:
        ctx.save()
        ctx.rotate(self.rot)
        ctx.translate(-78 + self.x, -70 + self.y)
        #ctx.translate(50, 40)

        #ctx.translate(-50, -40)
        #ctx.scale(100 / self.z, 100.0 / self.z)
        ctx.move_to(76.221727, 3.9788409).curve_to(
            94.027758, 31.627675, 91.038918, 37.561293, 94.653428, 48.340473
        ).rel_curve_to(
            25.783102, -3.90214, 30.783332, -1.52811, 47.230192, 4.252451
        ).rel_curve_to(
            -11.30184, 19.609496, -21.35729, 20.701768, -35.31018, 32.087063
        ).rel_curve_to(
            5.56219, 12.080061, 12.91196, 25.953973, 9.98735, 45.917643
        ).rel_curve_to(
            -19.768963, -4.59388, -22.879866, -10.12216, -40.896842, -23.93099
        ).rel_curve_to(
            -11.463256, 10.23025, -17.377386, 18.2378, -41.515124, 25.03533
        ).rel_curve_to(
            0.05756, -29.49286, 4.71903, -31.931936, 10.342734, -46.700913
        ).curve_to(
            33.174997, 77.048676, 19.482194, 71.413009, 8.8631648, 52.420793
        ).curve_to(
            27.471602, 45.126773, 38.877997, 45.9184, 56.349456, 48.518302
        ).curve_to(
            59.03275, 31.351935, 64.893201, 16.103886, 76.221727, 3.9788409
        ).close_path().fill()
        ctx.restore()

class SecondScreen(BaseView):
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

class App(Application):
    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)
        self.input = InputController()
        self.path = getattr(app_ctx, 'bundle_path', '/flash/apps/PetalHero')
        if not self.path:
            self.path = '/flash/apps/PetalHero'
        print(self.path)
        midiIn = midi.MidiInFile(MidiReader(None), self.path + '/notes.mid')
        #midiIn.read()

        self.flower = Flower(0, 0, 0.01)
        self.time = 0
        self.repeats = 0

    def draw(self, ctx: Context):
        ctx.rgb(*GO_GREEN)
        ctx.rgb(*PUSH_RED)

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
            self.vm.push(SecondScreen(), ViewTransitionSwipeLeft())

        if self.exiting:
            return

        #leds.set_brightness(32 - int(math.cos(self.time) * 32))
            
        led = -3
        for col in [RED, (1.0, 1.0, 0.0), BLUE, PUSH_RED, GO_GREEN]:
            for i in range(7):
                leds.set_rgb(led if led >= 0 else led + 40, *dim(col, -math.cos(self.time) / 2 + 0.5))
                led += 1
            leds.set_rgb(led, 0, 0, 0)
            led += 1
            
        leds.update()

    def on_enter(self, vm: Optional[ViewManager]) -> None:
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
    st3m.run.run_view(App(ApplicationContext()))
