from toydist.config_parser.parser import \
        AST

class PackageDescription:
    def __init__(self, name, version=None, summary=None, url=None,
            author=None, author_email=None, license=None, description=None,
            platforms=None, packages=None, py_modules=None, extensions=None):
        # XXX: should we check that we have sequences when required
        # (py_modules, etc...) ?

        # Package metadata
        self.name = name

        if not version:
            # Distutils default
            self.version = '0.0.0'
        else:
            self.version = version

        self.summary = summary
        self.url = url
        self.author = author
        self.author_email = author_email
        self.license = license
        self.description = description

        if not platforms:
            self.platforms = []
        else:
            self.platforms = platforms

        # Package content
        if not packages:
            self.packages = []
        else:
            self.packages = packages

        if not py_modules:
            self.py_modules = []
        else:
            self.py_modules = py_modules

        if not extensions:
            self.extensions = []
        else:
            self.extensions = extensions

    def to_dict(self):
        """Return a distutils.core.setup compatible dict."""
        d = {'name': self.name,
            'version': self.version,
            'description': self.summary,
            'url': self.url,
            'author': self.author,
            'author_email': self.author_email,
            'license': self.license,
            'long_description': self.description,
            'platforms': self.platforms,
            'py_modules': self.py_modules}

        return d

def _parse_static(cnt):
    """Parse a static file. cnt is assumed to be the content of the static file
    in one string"""
    ast = AST()
    ast.parse_string(cnt)
    return PackageDescription(**ast.to_dict())

def parse_static(filename):
    f = open(filename)
    try:
        cnt = "\n".join(f.readlines())
        return _parse_static(cnt)
    finally:
        f.close()

