import utils
import os

README = """Put your Petal Hero songs here.

Petal Hero is compatible with songs for Frets on Fire, but with
one caveat: you need to mix audio tracks and save them as MP3.
This should do:

  sox -m *.ogg -c 1 -C 64 -r 48000 song.mp3

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
