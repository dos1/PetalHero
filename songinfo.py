from configparser import ConfigParser
import os
import midi
import midireader

from midireader import difficulties, noteSet

class MidiInfoReader(midi.MidiOutStream):
  __slots__ = ("notes", )
    
  # We exit via this exception so that we don't need to read the whole file in
  class Done(Exception): pass
  
  def __init__(self):
    super().__init__()
    self.notes = set()

  def note_on(self, channel, note, velocity):
    self.notes.add(note)

class SongInfo(object):
  def __init__(self, dirName):
    infoFileName = dirName + "/song.ini"
    self.dirName       = dirName
    self.songName      = os.path.basename(os.path.dirname(infoFileName))
    self.fileName      = infoFileName
    self.info          = ConfigParser()
    self._difficulties = None

    try:
      self.info.read(infoFileName)
    except:
      pass

  def _set(self, attr, value):
    if not self.info.has_section("song"):
      self.info.add_section("song")
    if type(value) == str:
      value = value.encode(Config.encoding)
    else:
      value = str(value)
    self.info.set("song", attr, value)

  def _get(self, attr, type = None, default = ""):
    try:
      v = self.info.get("song", attr)
    except:
      v = default
    if v is not None and type:
      v = type(v)
    return v

  def getDifficulties(self):
    if self._difficulties is not None:
      return self._difficulties

    diffFileName = os.path.join(os.path.dirname(self.fileName), "diffs.pet")
    try:
      with open(diffFileName, "rb") as f:
        self._difficulties = []
        diffs = f.read(10)
        for b in diffs:
          self._difficulties.append(difficulties[int(b)])
      if not self._difficulties:
          #os.unlink(diffFileName) # unlink's broken
          raise Exception
      self._difficulties.sort(key = lambda a: a.id, reverse=True)
      return self._difficulties
    except Exception as e:
      pass

    # See which difficulties are available
    noteFileName = os.path.join(os.path.dirname(self.fileName), "notes.mid")
    info = MidiInfoReader()
    midiIn = midi.MidiInFile(info, noteFileName)
    try:
      midiIn.read()
    except MidiInfoReader.Done:
      pass
    
    diffset = set()
    for note in info.notes:
      if not note in noteSet:
          continue
      track, number = midireader.noteMap[note]
      diff = difficulties[track]
      if not diff in diffset:
          diffset.add(diff)
          if len(diffset) == len(difficulties):
              break
    self._difficulties = list(diffset)
    self._difficulties.sort(key = lambda a: a.id, reverse=True)
    #except Exception as e:
    #  print(e)
    #  return []
    return self._difficulties

  def saveDifficulties(self):
    if self._difficulties is None:
      return
    try:
      diffFileName = os.path.join(os.path.dirname(self.fileName), "diffs.pet")
      with open(diffFileName, "wb") as f:
        for diff in self._difficulties:
          f.write(bytes([diff.id]))
    except Exception as e:
      print(e)

  def getName(self):
    return self._get("name")

  def setName(self, value):
    self._set("name", value)

  def getArtist(self):
    return self._get("artist")
  
  def setArtist(self, value):
    self._set("artist", value)
    
  def getDelay(self):
    return self._get("delay", int, 0)
    
  def setDelay(self, value):
    return self._set("delay", value)
    
  name          = property(getName, setName)
  artist        = property(getArtist, setArtist)
  delay         = property(getDelay, setDelay)
  difficulties  = property(getDifficulties)
