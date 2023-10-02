import os

from .configparser import ConfigParser

from .midi import MidiOutStream, MidiInFile
from .midireader import difficulties, noteSet, noteMap

class MidiInfoReader(MidiOutStream):
  __slots__ = ("difficulties", "nTracks", "ignored", "trackNo")
      
  # We exit via this exception so that we don't need to read the whole file in
  class Done(Exception): pass
  
  def __init__(self):
    super().__init__()
    self.difficulties = set()
    self.ignored = False
    self.nTracks = 0
    self.trackNo = -1
    
  def start_of_track(self, track):
    self.trackNo = track

  def header(self, format, nTracks, division):
    self.nTracks = nTracks

  def sequence_name(self, val):
    name = ''.join(list(map(chr, val)))
    self.ignored = name != "PART GUITAR" and self.nTracks > 2
    if self.difficulties:
      raise MidiInfoReader.Done()
    return self.ignored

  def note_on(self, channel, note, velocity):
    if not self.ignored:
      if not note in noteMap:
        return
      self.difficulties.add(difficulties[noteMap[note][0]])
      if len(self.difficulties) == len(difficulties):
        raise MidiInfoReader.Done()

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
    except Exception as e:
      print(f"Exception while reading {infoFileName}: {e}")

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

    diffFileName = os.path.join(os.path.dirname(self.fileName), ".diff.pet")
    try:
      with open(diffFileName, "rb") as f:
        self._difficulties = []
        diffs = f.read(10)
        for b in diffs:
          self._difficulties.append(difficulties[int(b)])
      #if not self._difficulties:
      #    os.unlink(diffFileName) # unlink's broken
      #    raise Exception
      self._difficulties.sort(key = lambda a: a.id, reverse=True)
      return self._difficulties
    except Exception as e:
      pass

    # See which difficulties are available
    noteFileName = os.path.join(os.path.dirname(self.fileName), "notes.mid")
    info = MidiInfoReader()
    midiIn = MidiInFile(info, noteFileName)
    try:
      midiIn.read()
    except MidiInfoReader.Done:
      pass
    
    self._difficulties = list(info.difficulties)
    self._difficulties.sort(key = lambda a: a.id, reverse=True)
    #except Exception as e:
    #  print(e)
    #  return []
    return self._difficulties

  def saveDifficulties(self):
    if self._difficulties is None:
      return
    try:
      diffFileName = os.path.join(os.path.dirname(self.fileName), ".diff.pet")
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
  
  def getPreview(self):
    preview = self._get("preview_start_time", int, None)
    length = self._get("song_length", int, None)
    if preview is None or preview < 0 or length is None or length <= 0:
        return 0.1
    return preview / length
    
  name          = property(getName, setName)
  artist        = property(getArtist, setArtist)
  delay         = property(getDelay, setDelay)
  difficulties  = property(getDifficulties)
  preview       = property(getPreview)
