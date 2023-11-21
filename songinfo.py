import os
import sys

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

  def load(self):
    return self

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

  def readDifficulties(self):
    if self._difficulties is not None:
      return self._difficulties

    diffFileName = os.path.join(os.path.dirname(self.fileName), ".diff.pet")
    try:
      diffs = []
      with open(diffFileName, "rb") as f:
        magic = f.read(6)
        assert(magic == b"PHDIFF")
        ver = f.read(1)
        assert(ver == b"\0")
        length = f.read(1)[0]
        difflist = f.read(length)
        assert(len(difflist) == length)
        for b in difflist:
          diffs.append(difficulties[b])
      diffs.sort(key = lambda a: a.id, reverse=True)
      self._difficulties = diffs
      return self._difficulties
    except AssertionError as e:
      print(f"Assertion failed while processing {self.fileName}")
      sys.print_exception(e)
      os.unlink(diffFileName)
    except Exception as e:
      print(f"Error while processing {self.fileName}")
      sys.print_exception(e)

  def getDifficulties(self):
    if self._difficulties is not None:
      return self._difficulties

    diffFileName = os.path.join(os.path.dirname(self.fileName), ".diff.pet")
    if os.path.exists(diffFileName):
        self.readDifficulties()
        if self._difficulties is not None:
          return self._difficulties

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

    self.saveDifficulties()

    return self._difficulties

  def saveDifficulties(self):
    if self._difficulties is None:
      return

    try:
      diffFileName = os.path.join(os.path.dirname(self.fileName), ".diff.pet")
      with open(diffFileName, "wb") as f:
        f.write(b"PHDIFF\0")
        f.write(bytes((len(self._difficulties),)))
        for diff in self._difficulties:
          f.write(bytes([diff.id]))
    except Exception as e:
      sys.print_exception(e)

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
