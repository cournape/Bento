from distutils.core import \
        Extension as DistExtension

class Extension(DistExtension):
    def __repr__(self):
        return "Extension(%s, sources=%s)" % (self.name, self.sources)
