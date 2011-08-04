from bento.core.errors \
    import \
        InvalidPackage

_METADATA_FIELDS = ["name", "version", "summary", "url", "author",
        "author_email", "maintainer", "maintainer_email", "license", "description",
        "platforms", "install_requires", "build_requires", "download_url",
        "classifiers", "top_levels", "description_from_file"]

def _set_metadata(obj, name, version=None, summary=None, url=None,
        author=None, author_email=None, maintainer=None,
        maintainer_email=None, license=None, description=None,
        platforms=None, install_requires=None, build_requires=None,
        download_url=None, classifiers=None, top_levels=None, description_from_file=None):
    obj.name = name

    obj.version = version

    obj.summary = summary
    obj.url = url
    obj.download_url = download_url
    obj.author = author
    obj.author_email = author_email
    obj.maintainer = maintainer
    obj.maintainer_email = maintainer_email
    obj.license = license
    obj.description = description
    obj.description_from_file = description_from_file

    if not install_requires:
        obj.install_requires = []
    else:
        obj.install_requires = install_requires

    if not build_requires:
        obj.build_requires = []
    else:
        obj.build_requires = build_requires

    if not platforms:
        obj.platforms = []
    else:
        obj.platforms = platforms

    if not classifiers:
        obj.classifiers = []
    else:
        obj.classifiers = classifiers

    if not top_levels:
        obj.top_levels = []
    else:
        obj.top_levels = top_levels

    return obj

class PackageMetadata(object):
    metadata_attributes = _METADATA_FIELDS + ["fullname", "contact", "contact_email"]

    @classmethod
    def from_ipkg(cls, ipkg):
        return cls(**ipkg.meta)

    @classmethod
    def from_package(cls, pkg):
        kw = {}
        for k in _METADATA_FIELDS:
            if hasattr(pkg, k):
                kw[k] = getattr(pkg, k)
        return cls(**kw)

    def __init__(self, name, version=None, summary=None, url=None,
            author=None, author_email=None, maintainer=None,
            maintainer_email=None, license=None, description=None,
            platforms=None, install_requires=None, build_requires=None,
            download_url=None, classifiers=None, top_levels=None, description_from_file=None):
        # Package metadata
        _args = locals()
        kw = dict([(k, _args[k]) for k in _METADATA_FIELDS if k in _args])
        _set_metadata(self, **kw)

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
