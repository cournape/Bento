from bento.private.version \
    import \
        NormalizedVersion, is_valid_version, suggest_normalized_version
from bento.core.errors \
    import \
        InvalidPackage

_METADATA_EXPLICIT = ["name", "version", "summary", "url", "author",
        "author_email", "maintainer", "maintainer_email", "license", "description",
        "platforms", "install_requires", "build_requires", "download_url",
        "classifiers", "top_levels", "description_from_file", "keywords"]

_METADATA_FIELDS = _METADATA_EXPLICIT + ["version_major", "version_minor",
                                         "version_micro", "version_postdev"]

def _set_metadata(obj, name, version=None, summary=None, url=None,
        author=None, author_email=None, maintainer=None,
        maintainer_email=None, license=None, description=None,
        platforms=None, install_requires=None, build_requires=None,
        download_url=None, classifiers=None, top_levels=None,
        description_from_file=None, keywords=None):
    obj.name = name

    obj.version = version

    if version is None:
        obj.version_major = 0
        obj.version_minor = 0
        obj.version_micro = 0
        obj.version_postdev = ""
    else:
        if not is_valid_version(version):
            raise InvalidPackage("Invalid version: %r (suggested version: %s)" \
                                 % (version, suggest_normalized_version(version)))
        v = NormalizedVersion(version)
        obj.version_major = v.parts[0][0]
        obj.version_minor = v.parts[0][1]
        if len(v.parts[0]) > 2:
            obj.version_micro = v.parts[0][2]
        else:
            obj.version_micro = 0
        # FIXME: look at distutils version stuff more carefully
        obj.version_postdev = ""
        #if v.parts[1] != ('f',):
        #    raise InvalidPackage("Unsupported version: %r (prerelease part)" % (version,))
        #if v.parts[2] == ('f',):
        #    obj.version_postdev = ""
        #else:
        #    obj.version_postdev = "".join([str(i) for i in v.parts[2]])

    # FIXME: one should set metadata default elsewhere, and suggest good values
    # for developers
    obj.summary = summary or ""
    obj.url = url or ""
    obj.download_url = download_url or ""
    obj.author = author or ""
    obj.author_email = author_email or ""
    obj.maintainer = maintainer or ""
    obj.maintainer_email = maintainer_email or ""
    obj.license = license or ""
    obj.description = description or ""
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

    if not keywords:
        obj.keywords = []
    else:
        obj.keywords = keywords

    return obj

class PackageMetadata(object):
    metadata_attributes = _METADATA_FIELDS + ["fullname", "contact", "contact_email"]

    @classmethod
    def from_ipkg(cls, ipkg):
        return cls(**ipkg.meta)

    @classmethod
    def from_package(cls, pkg):
        kw = {}
        for k in _METADATA_EXPLICIT:
            if hasattr(pkg, k):
                kw[k] = getattr(pkg, k)
        return cls(**kw)

    def __init__(self, name, version=None, summary=None, url=None,
            author=None, author_email=None, maintainer=None,
            maintainer_email=None, license=None, description=None,
            platforms=None, install_requires=None, build_requires=None,
            download_url=None, classifiers=None, top_levels=None,
            description_from_file=None, keywords=None):
        # Package metadata
        _args = locals()
        kw = dict([(k, _args[k]) for k in _METADATA_FIELDS if k in _args])
        _set_metadata(self, **kw)

        # FIXME: not implemented yet
        self.provides = []
        self.obsoletes = []

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
