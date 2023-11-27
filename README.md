# Petal Hero

Rhythm game for the [flow3r badge](https://flow3r.garden/).

Created by [Sebastian Krzyszkowiak](https://dosowisko.net).

## Songs

*Petal Hero* is compatible with songs for Frets on Fire, FoFiX, Performous,
Phase Shift and Clone Hero (MIDI) that contain a guitar track, but with one
caveat: you need to mix audio tracks together and save them as MP3.

This should do:

```sh
sox *.ogg -m -G -c 1 -C 128 -r 48k --norm=-3 song.mp3
```

Some rips may need to be resampled first:

```sh
for i in *.ogg; do sox $i -G -r 48k $i.flac; done
sox *.flac -m -G -c 1 -C 128 -r 4/8k --norm=-3 song.mp3
```

You need *song.ini*, *song.mp3* and *notes.mid* in the song directory.

Songs in *.chart* format (and some others) can be converted using [EOF](https://github.com/raynebc/editor-on-fire).

The "Starter Pack" of songs can be downloaded over Wi-Fi from the game, or manually
from [the song repository](https://git.flow3r.garden/dos/PetalHero-songs/).

Some places to find charted songs at:
 - https://chorus.fightthe.pw/
 - https://db.c3universe.com/songs/
 - https://sourceforge.net/p/fretsonfire/code/HEAD/tarball?path=/trunk/data/songs

## License

*Petal Hero* is licensed under the GNU General Public License version 3 or later.

Sound assets and parts of the code come from *Frets on Fire* by Sami Kyöstilä,
Tommi Inkilä, Joonas Kerttula and Max M., originally licensed under the GNU
General Public License version 2 or later.
