from .diacritics import diacritic_map

KEYS = ["name", "artist", "delay", "preview_start_time", "song_length"]

class ConfigParser:
    def __init__(self):
        self.config_dict = {}

    def has_section(self, section):
        return True

    def read(self, filename=None, fp=None):
        """Read and parse a filename or a list of filenames."""
        if not fp and not filename:
            print("ERROR : no filename and no fp")
            raise
        elif not fp and filename:
            fp = open(filename)

        content = fp.read().splitlines()
        
        for line in content:
            line = line.strip()
            if "=" in line:
                key, value = line.split('=', 1)
                key = key.lower().strip()
                if key in KEYS:
                    self.config_dict[key] = "".join(map(lambda x: diacritic_map[x] if x in diacritic_map else x, value.strip()))
            if len(self.config_dict) == len(KEYS):
                break

        fp.close()

    def get(self, section, option):
        return self.config_dict[option]
