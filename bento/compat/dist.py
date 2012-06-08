import sys
import distutils.dist 

from distutils.util \
    import \
        check_environ, strtobool, rfc822_escape

# Taken from python 2.6.5
PKG_INFO_ENCODING = 'utf-8'
class _DistributionMetadata:
    """Dummy class to hold the distribution meta-data: name, version,
    author, and so forth.
    """

    _METHOD_BASENAMES = ("name", "version", "author", "author_email",
                         "maintainer", "maintainer_email", "url",
                         "license", "description", "long_description",
                         "keywords", "platforms", "fullname", "contact",
                         "contact_email", "license", "classifiers",
                         "download_url",
                         # PEP 314
                         "provides", "requires", "obsoletes",
                         )

    def __init__ (self):
        self.name = None
        self.version = None
        self.author = None
        self.author_email = None
        self.maintainer = None
        self.maintainer_email = None
        self.url = None
        self.license = None
        self.description = None
        self.long_description = None
        self.keywords = None
        self.platforms = None
        self.classifiers = None
        self.download_url = None
        # PEP 314
        self.provides = None
        self.requires = None
        self.obsoletes = None

    def write_pkg_info (self, base_dir):
        """Write the PKG-INFO file into the release tree.
        """
        pkg_info = open( os.path.join(base_dir, 'PKG-INFO'), 'w')

        self.write_pkg_file(pkg_info)

        pkg_info.close()

    # write_pkg_info ()

    def write_pkg_file (self, file):
        """Write the PKG-INFO format data to a file object.
        """
        version = '1.0'
        if (self.provides or self.requires or self.obsoletes or
            self.classifiers or self.download_url):
            version = '1.1'

        self._write_field(file, 'Metadata-Version', version)
        self._write_field(file, 'Name', self.get_name())
        self._write_field(file, 'Version', self.get_version())
        self._write_field(file, 'Summary', self.get_description())
        self._write_field(file, 'Home-page', self.get_url())
        self._write_field(file, 'Author', self.get_contact())
        self._write_field(file, 'Author-email', self.get_contact_email())
        self._write_field(file, 'License', self.get_license())
        if self.download_url:
            self._write_field(file, 'Download-URL', self.download_url)

        long_desc = rfc822_escape( self.get_long_description())
        self._write_field(file, 'Description', long_desc)

        keywords = ",".join(self.get_keywords())
        if keywords:
            self._write_field(file, 'Keywords', keywords)

        self._write_list(file, 'Platform', self.get_platforms())
        self._write_list(file, 'Classifier', self.get_classifiers())

        # PEP 314
        self._write_list(file, 'Requires', self.get_requires())
        self._write_list(file, 'Provides', self.get_provides())
        self._write_list(file, 'Obsoletes', self.get_obsoletes())

    def _write_field(self, file, name, value):
        file.write('%s: %s\n' % (name, self._encode_field(value)))

    def _write_list (self, file, name, values):

        for value in values:
            self._write_field(file, name, value)

    def _encode_field(self, value):
        if value is None:
            return None
        if isinstance(value, unicode):
            return value.encode(PKG_INFO_ENCODING)
        return str(value)

    # -- Metadata query methods ----------------------------------------

    def get_name (self):
        return self.name or "UNKNOWN"

    def get_version(self):
        return self.version or "0.0.0"

    def get_fullname (self):
        return "%s-%s" % (self.get_name(), self.get_version())

    def get_author(self):
        return self._encode_field(self.author) or "UNKNOWN"

    def get_author_email(self):
        return self.author_email or "UNKNOWN"

    def get_maintainer(self):
        return self._encode_field(self.maintainer) or "UNKNOWN"

    def get_maintainer_email(self):
        return self.maintainer_email or "UNKNOWN"

    def get_contact(self):
        return (self._encode_field(self.maintainer) or
                self._encode_field(self.author) or "UNKNOWN")

    def get_contact_email(self):
        return (self.maintainer_email or
                self.author_email or
                "UNKNOWN")

    def get_url(self):
        return self.url or "UNKNOWN"

    def get_license(self):
        return self.license or "UNKNOWN"
    get_licence = get_license

    def get_description(self):
        return self._encode_field(self.description) or "UNKNOWN"

    def get_long_description(self):
        return self._encode_field(self.long_description) or "UNKNOWN"

    def get_keywords(self):
        return self.keywords or []

    def get_platforms(self):
        return self.platforms or ["UNKNOWN"]

    def get_classifiers(self):
        return self.classifiers or []

    def get_download_url(self):
        return self.download_url or "UNKNOWN"

    # PEP 314

    def get_requires(self):
        return self.requires or []

    def set_requires(self, value):
        import distutils.versionpredicate
        for v in value:
            distutils.versionpredicate.VersionPredicate(v)
        self.requires = value

    def get_provides(self):
        return self.provides or []

    def set_provides(self, value):
        value = [v.strip() for v in value]
        for v in value:
            import distutils.versionpredicate
            distutils.versionpredicate.split_provision(v)
        self.provides = value

    def get_obsoletes(self):
        return self.obsoletes or []

    def set_obsoletes(self, value):
        import distutils.versionpredicate
        for v in value:
            distutils.versionpredicate.VersionPredicate(v)
        self.obsoletes = value

if sys.version_info[0] < 3:
    DistributionMetadata = _DistributionMetadata
else:
    DistributionMetadata = distutils.dist.DistributionMetadata
