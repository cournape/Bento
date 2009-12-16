class PackageMetadata(object):
    @classmethod
    def from_installed_pkg_description(cls, ipkg):
        return cls(**ipkg.meta)

    def __init__(self, name, version=None, summary=None, url=None,
            author=None, author_email=None, maintainer=None,
            maintainer_email=None, license=None, description=None,
            platforms=None, install_requires=None, build_requires=None,
            download_url=None, classifiers=None, top_levels=None):
        self.name = name

        if not version:
            # Distutils default
            self.version = '0.0.0'
        else:
            self.version = version

        self.summary = summary
        self.url = url
        self.download_url = download_url
        self.author = author
        self.author_email = author_email
        self.maintainer = maintainer
        self.maintainer_email = maintainer_email
        self.license = license
        self.description = description

        if not install_requires:
            self.install_requires = []
        else:
            self.install_requires = install_requires

        if not build_requires:
            self.build_requires = []
        else:
            self.build_requires = build_requires

        if not platforms:
            self.platforms = []
        else:
            self.platforms = platforms

        if not classifiers:
            self.classifiers = []
        else:
            self.classifiers = classifiers

        if not top_levels:
            self.top_levels = []
        else:
            self.top_levels = top_levels

        # FIXME: not implemented yet
        self.provides = []
        self.obsoletes = []
        self.keywords = []

    @property
    def fullname(self):
        return "%s-%s" % (self.name, self.version)

    @property
    def contact(self):
        return (self.maintainer or
                self.author or
                "UNKNOWN")

    @property
    def contact_email(self):
        return (self.maintainer_email or
                self.author_email or
                "UNKNOWN")
