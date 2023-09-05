import midi

AMAZING_DIFFICULTY      = 0
MEDIUM_DIFFICULTY       = 1
EASY_DIFFICULTY         = 2
SUPAEASY_DIFFICULTY     = 3

baseNotes = {
  0x60: AMAZING_DIFFICULTY,
  0x54: MEDIUM_DIFFICULTY,
  0x48: EASY_DIFFICULTY,
  0x3c: SUPAEASY_DIFFICULTY
}

noteMap = {}
for basenote, diff in baseNotes.items():
  for note in range(5):
    noteMap[basenote + note] = (diff, note)

reverseNoteMap = dict([(v, k) for k, v in list(noteMap.items())])

class Event:
  def __init__(self, length):
    self.length = length

class Note(Event):
  def __init__(self, number, length, special = False, tappable = False):
    super().__init__(length)
    self.number   = number
    self.played   = False
    self.special  = special
    self.tappable = tappable
    
  def __repr__(self):
    return "<Note #%d length: %d>" % (self.number, self.length)

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
