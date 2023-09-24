import utils
import os

README = """Put your Petal Hero songs here.

Petal Hero is compatible with songs for Frets on Fire, FoFiX, Performous,
Phase Shift and Clone Hero (MIDI) that contain a guitar track, but with one
caveat: you need to mix audio tracks and save them as MP3.

This should do:

  sox -m *.ogg -c 1 -C 128 -r 48k song.mp3 norm -3

You need song.ini, song.mp3 and notes.mid in the song directory.
"""

def install():
    if not utils.sd_card_present():
        return

    try:
        l = os.listdir("/sd/PetalHero")
    except Exception as e:
        os.mkdir("/sd/PetalHero")
        l = []

    if not "README" in l:
        with open("/sd/PetalHero/README", "w") as file:
            file.write(README)
