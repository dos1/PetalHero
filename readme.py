from . import utils
import os
#from st3m.utils import save_file_if_changed

README = """Put your Petal Hero songs here.

Petal Hero is compatible with songs for Frets on Fire, FoFiX, Performous,
Phase Shift and Clone Hero (MIDI) that contain a guitar track, but with one
caveat: you need to mix audio tracks together and save them as MP3.

This should do:

  sox -m *.ogg -c 1 -C 128 -r 48k song.mp3 norm -3

You need song.ini, song.mp3 and notes.mid in the song directory.

Songs in .chart format (and some others) can be converted using EOF:
https://github.com/raynebc/editor-on-fire

Some places to find charted songs:
 - https://chorus.fightthe.pw/
 - https://db.c3universe.com/songs/
 - https://docs.google.com/spreadsheets/u/0/d/13B823ukxdVMocowo1s5XnT3tzciOfruhUVePENKc01o/htmlview

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

    if not "README" in l:
        with open("/sd/PetalHero/README", "w") as file:
            file.write(README)
    #save_file_if_changed("/sd/PetalHero/README", README)
