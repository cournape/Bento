from distutils.core import \
        Extension as DistExtension

class Extension(DistExtension):
    def __repr__(self):
        return "Extension %s (sources are %s)" % (self.name, ",".join(self.sources))
