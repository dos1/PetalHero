from . import utils
import os
try:
    from st3m.utils import save_file_if_changed
except ImportError:
    pass

README = """Put your Petal Hero songs here.

Petal Hero is compatible with songs for Frets on Fire, FoFiX, Performous,
Phase Shift and Clone Hero (MIDI) that contain a guitar track, but with one
caveat: you need to mix audio tracks together and save them as MP3.

This should do:

  sox *.ogg -m -G -c 1 -C 128 -r 48k --norm=-3 song.mp3

Some rips may need to be resampled first:

  for i in *.ogg; do sox $i -G -r 48k $i.flac; done
  sox *.flac -m -G -c 1 -C 128 -r 48k --norm=-3 song.mp3

You need song.ini, song.mp3 and notes.mid in the song directory.

The "Starter Pack" of songs can be downloaded over Wi-Fi from the game,
or manually from https://git.flow3r.garden/dos/PetalHero-songs/

Songs in .chart format (and some others) can be converted using EOF:
https://github.com/raynebc/editor-on-fire

Some places to find charted songs at:
 - https://chorus.fightthe.pw/
 - https://db.c3universe.com/songs/
 - https://sourceforge.net/p/fretsonfire/code/HEAD/tarball?path=/trunk/data/songs

Have fun!
"""

def install():
    if not utils.sd_card_present():
        return

    try:
        l = os.listdir("/sd/PetalHero")
    except Exception as e:
        try:
            os.mkdir("/sd/PetalHero")
        except:
            print("Could not create /sd/PetalHero dir!")
            return
        l = []

    save_file_if_changed("/sd/PetalHero/README.TXT", README)
