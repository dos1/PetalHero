from . import midi

AMAZING_DIFFICULTY      = 0
MEDIUM_DIFFICULTY       = 1
EASY_DIFFICULTY         = 2
SUPAEASY_DIFFICULTY     = 3

class Difficulty:
  def __init__(self, id, text):
    self.id   = id
    self.text = text
    
  def __str__(self):
    return self.text

  def __repr__(self):
    return self.text

difficulties = {
  SUPAEASY_DIFFICULTY: Difficulty(SUPAEASY_DIFFICULTY, "Easy"),
  EASY_DIFFICULTY:     Difficulty(EASY_DIFFICULTY,     "Medium"),
  MEDIUM_DIFFICULTY:   Difficulty(MEDIUM_DIFFICULTY,   "Hard"),
  AMAZING_DIFFICULTY:  Difficulty(AMAZING_DIFFICULTY,  "Expert"),
}

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

noteSet = set(noteMap.keys())

class Event:
  __slots__ = ("length", "time")

  def __init__(self, time, length):
    self.length = length
    self.time = time

class Note(Event):
  __slots__ = ("number", "played", "missed", "ghost")

  def __init__(self, time, number, length, special = False):
    super().__init__(time, length)
    self.number   = number
    self.played   = False
    self.missed   = False
    self.ghost    = False

  def __repr__(self):
    return "<Note #%d time: %d length: %d>" % (self.number, self.time, self.length)

class Tempo(Event):
  __slots__ = ("bpm",)

  def __init__(self, bpm):
    super().__init__(None, 0)
    self.bpm = bpm

  def __repr__(self):
    return "<%d bpm>" % self.bpm

class Track:
  granularity = 500
  
  def __init__(self):
    self.events = []
    #self.allEvents = set()

  def addEvent(self, time, event):
    for t in range(int(time / self.granularity), int((time + event.length) / self.granularity) + 1):
      if len(self.events) < t + 1:
        n = t + 1 - len(self.events)
        n *= 8
        for n in range(n):
          self.events.append(set())
      self.events[t].add(event)
    #print(len(self.allEvents), event)
    #self.allEvents.add(event)

  def getEvents(self, startTime, endTime, events):
    t1, t2 = [int(x) for x in [startTime / self.granularity, endTime / self.granularity + 1]]
    if t1 > t2:
      t1, t2 = t2, t1

    events.clear()
    for t in range(max(t1, 0), min(len(self.events), t2)):
      for event in self.events[t]:
        events.add(event)
    return events

  def getAllEvents(self):
    allEvents = set()
    for i in range(len(self.events)):
        allEvents.update(self.events[i])
    return allEvents

  def reset(self):
    for eventList in self.events:
      for event in eventList:
        if isinstance(event, Note):
          event.played = False
          event.missed = False

class MidiReader(midi.MidiOutStream):
  def __init__(self, difficulty):
    super().__init__()
    self.bpm = 0
    self.heldNotes = {}
    self.velocity  = {}
    self.ticksPerBeat = 480
    self.tempoMarkers = []
    self.beats = []
    #self.tracks        = [Track() for t in range(len(difficulties))]
    self.difficulty = difficulty
    self.track = Track()
    self.nTracks = -1
    self.ignored = False
    self.track_name = None
    
    self.current_tempo_marker = 0
    self.scaledTime = 0

  def addEvent(self, track, event):
    time = event.time
    if time is None:
      time = self.abs_time()
    assert time >= 0
    #print('addEvent', track, event, time)
    if track is None or track == self.difficulty.id:
      self.track.addEvent(time, event)
    #if track is None:
    #  for t in self.tracks:
    #    t.addEvent(time, event)
    #elif track < len(self.tracks):
    #  self.tracks[track].addEvent(time, event)

  def ticksToBeats(self, ticks, bpm):
    return (60000.0 * ticks) / (bpm * self.ticksPerBeat)

  def abs_time(self):
    if self.bpm:
      currentTime = midi.MidiOutStream.abs_time(self)

      if self.current_tempo_marker == 0:
        tempoMarkerTime, currentBpm = 0.0, self.bpm 
      else:
        tempoMarkerTime, currentBpm = self.tempoMarkers[self.current_tempo_marker - 1]

      while len(self.tempoMarkers) > self.current_tempo_marker:
        time, bpm = self.tempoMarkers[self.current_tempo_marker]
        if time > currentTime:
          break
        self.scaledTime += self.ticksToBeats(time - tempoMarkerTime, currentBpm)
        self.current_tempo_marker += 1
        tempoMarkerTime, currentBpm = time, bpm

      return self.scaledTime + self.ticksToBeats(currentTime - tempoMarkerTime, currentBpm)
    return 0.0

  def header(self, format, nTracks, division):
    self.ticksPerBeat = division
    self.nTracks = nTracks
    
  def tempo(self, value):
    # TODO: should tempoMarkers list get sorted in case of tempo events scattered
    # across various tracks?

    bpm = 60.0 * 10.0**6 / value
    if not self.tempoMarkers or bpm != self.tempoMarkers[-1][1]:
        self.tempoMarkers.append((midi.MidiOutStream.abs_time(self), bpm))
        #print(self.tempoMarkers)
    if not self.bpm:
      self.bpm = bpm
      self.period = 60000.0 / self.bpm
    #print('bpm', bpm)
    #self.addEvent(None, Tempo(bpm))

  def sequence_name(self, val):
    name = ''.join(list(map(chr, val)))
    #print(name)
    self.track_name = name
    self.ignored = name != "PART GUITAR" and name != "BEAT" and self.nTracks > 2
    self.current_tempo_marker = 0
    self.scaledTime = 0
    return self.ignored

  def note_on(self, channel, note, velocity):
    if self.ignored: return
    #print("note_on", channel, note, velocity, self.abs_time())
    if self.track_name == "BEAT":
      self.beats.append(self.abs_time())
      return
    if not note in noteMap:
      return
    if noteMap[note][0] != self.difficulty.id:
      return
    self.velocity[note] = velocity
    self.heldNotes[(self.get_current_track(), channel, note)] = self.abs_time()

  def note_off(self, channel, note, velocity):
    if self.ignored: return
    #print("note_off", channel, note, velocity, self.abs_time())
    if not note in noteMap:
      return
    if noteMap[note][0] != self.difficulty.id:
      return
    try:
      startTime = self.heldNotes[(self.get_current_track(), channel, note)]
      endTime   = self.abs_time()
      del self.heldNotes[(self.get_current_track(), channel, note)]
      track, number = noteMap[note]
      self.addEvent(track, Note(startTime, number, endTime - startTime, special = self.velocity[note] == 127))
    except KeyError:
      print("MIDI note 0x%x on channel %d ending at %d was never started." % (note, channel, self.abs_time()))
