class Extension(object):
    def __init__(self, name, src):
        self.name = name
        self.src = src

    def __repr__(self):
        return "Extension %s (sources are %s)" % (self.name, ",".join(self.src))

