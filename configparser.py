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

        content = fp.read().split('\n')
        
        for line in content:
            line = line.strip()
            if "=" in line:
                key, value = line.split('=')
                self.config_dict[key.lower().strip()] = value.strip()
            if "name" in self.config_dict and "artist" in self.config_dict and "delay" in self.config_dict:
                break

        fp.close()

    def get(self, section, option):
        return self.config_dict[option]
