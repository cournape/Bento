from toydist.package import \
        PackageDescription
from toydist.cabal_parser.misc import \
        parse_executable

def distutils_to_package_description(dist):
    data = {}

    data['name'] = dist.get_name()
    data['version'] = dist.get_version()
    data['author'] = dist.get_author()
    data['author_email'] = dist.get_author_email()
    data['maintainer'] = dist.get_contact()
    data['maintainer_email'] = dist.get_contact_email()
    data['summary'] = dist.get_description()
    data['description'] = dist.get_long_description()
    data['license'] = dist.get_license()
    data['platforms'] = dist.get_platforms()

    data['download_url'] = dist.get_download_url()
    data['url'] = dist.get_url()

    # XXX: reliable way to detect whether Distribution was monkey-patched by
    # setuptools
    try:
        reqs = getattr(dist, "install_requires")
        # FIXME: how to detect this correctly
        if issubclass(type(reqs), (str, unicode)):
            reqs = [reqs]
        data['install_requires'] = reqs
    except AttributeError:
        pass

    data['py_modules'] = dist.py_modules
    data['packages'] = dist.packages
    data['extensions'] = dist.ext_modules
    data['classifiers'] = dist.get_classifiers()

    data["executables"] = {}
    if hasattr(dist, "entry_points"):
        try:
            console_scripts = dist.entry_points["console_scripts"]
        except KeyError:
            console_scripts = []
        for entry in console_scripts:
            if not "=" in entry:
                raise ValueError("Could not parse entry in console_scripts %s" % entry)
            name, value = [i.strip() for i in entry.split("=", 1)]
            module, function = parse_executable(value)
            data["executables"][name] = {"module": module, "function": function}

    return PackageDescription(**data)

_DIST_CONV_DICT = {
    "long_description": lambda meta: meta.description,
    "description": lambda meta: meta.summary,
    # TODO: keywords not implemented yet
    "keywords": lambda meta: [],
    "fullname": lambda meta: "%s-%s" % (meta.name, meta.version),
    "contact": lambda meta: (meta.maintainer or
                             meta.author or
                             "UNKNOWN"),
    "contact_email": lambda meta: (meta.maintainer_email or
                                   meta.author_email or
                                   "UNKNOWN"),
    "requires": lambda meta: meta.install_requires
}

def to_distutils_meta(meta):
    from distutils.dist import DistributionMetadata
    ret = DistributionMetadata()
    for m in ret._METHOD_BASENAMES:
        try:
            val = _DIST_CONV_DICT[m](meta)
        except KeyError:
            val = getattr(meta, m)
        setattr(ret, m, val)

    return ret

def write_pkg_info(pkg, file):
    dist_meta = to_distutils_meta(pkg)
    dist_meta.write_pkg_file(file)
