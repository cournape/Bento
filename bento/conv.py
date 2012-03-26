import os

import bento.core.node

from bento.core.errors import \
        InvalidPackage
from bento.core import \
        PackageDescription
from bento.core.pkg_objects import \
        Executable
from bento.core.utils import \
        is_string

_PKG_TO_DIST = {
        "ext_modules": lambda pkg: [v for v  in \
                                    pkg.extensions.values()],
        "platforms": lambda pkg: [v for v  in pkg.platforms],
        "packages": lambda pkg: [v for v  in pkg.packages],
        "py_modules": lambda pkg: [v for v  in pkg.py_modules],
}

_META_PKG_TO_DIST = {}
def _setup():
    for k in ["name", "version", "url", "author", "author_email", "maintainer",
              "maintainer_email", "license", "download_url"]:
        def _f(attr):
            return lambda pkg: getattr(pkg, attr)
        _META_PKG_TO_DIST[k] = _f(k)
    _META_PKG_TO_DIST["long_description"] = lambda pkg: pkg.description
    _META_PKG_TO_DIST["description"] = lambda pkg: pkg.summary
_setup()
_PKG_TO_DIST.update(_META_PKG_TO_DIST)

def pkg_to_distutils_meta(pkg):
    """Obtain meta data information from pkg into a dictionary which may be
    used directly as an argument for setup function in distutils."""
    d = {}
    for k, v in _META_PKG_TO_DIST.items():
        d[k] = v(pkg)
    return d

def pkg_to_distutils(pkg):
    """Convert PackageDescription instance to a dict which may be used
    as argument to distutils/setuptools setup function."""
    d = {}

    for k, v in _PKG_TO_DIST.items():
        d[k] = v(pkg)

    return d

def validate_package(pkg_name, base_node):
    """Given a python package name, check whether it is indeed an existing
    package.

    Package is looked relatively to base_node."""
    # XXX: this function is wrong - use the code from setuptools
    pkg_dir = pkg_name.replace(".", os.path.sep)
    pkg_node = base_node.find_node(pkg_dir)
    if pkg_node is None:
        raise InvalidPackage("directory %s in %s does not exist" % (pkg_dir, base_node.abspath()))
    init = pkg_node.find_node('__init__.py')
    if init is None:
        raise InvalidPackage(
                "Missing __init__.py in package %s (in directory %s)"
                % (pkg_name, base_node.abspath()))
    return pkg_node

def find_package(pkg_name, base_node):
    """Given a python package name, find all its modules relatively to
    base_node."""
    pkg_node = validate_package(pkg_name, base_node)
    ret = []
    for f in pkg_node.listdir():
        if f.endswith(".py"):
            node = pkg_node.find_node(f)
            ret.append(node.path_from(base_node))
    return ret

def validate_packages(pkgs, top):
    ret_pkgs = []
    for pkg in pkgs:
        try:
            validate_package(pkg, top)
        except InvalidPackage:
            # FIXME: add the package as data here
            pass
        else:
            ret_pkgs.append(pkg)
    return ret_pkgs

def distutils_to_package_description(dist):
    root = bento.core.node.Node("", None)
    top = root.find_dir(os.getcwd())

    data = {}

    data['name'] = dist.get_name()
    data['version'] = dist.get_version()
    data['author'] = dist.get_author()
    data['author_email'] = dist.get_author_email()
    data['maintainer'] = dist.get_contact()
    data['maintainer_email'] = dist.get_contact_email()
    data['summary'] = dist.get_description()
    data['description'] = dist.get_long_description().replace("#", "\#")
    data['license'] = dist.get_license()
    data['platforms'] = dist.get_platforms()

    data['download_url'] = dist.get_download_url()
    data['url'] = dist.get_url()

    # XXX: reliable way to detect whether Distribution was monkey-patched by
    # setuptools
    try:
        reqs = getattr(dist, "install_requires")
        # FIXME: how to detect this correctly
        if is_string(reqs):
            reqs = [reqs]
        data['install_requires'] = reqs
    except AttributeError:
        pass

    if dist.py_modules is None:
        data['py_modules'] = []
    else:
        data['py_modules'] = dist.py_modules
    if dist.packages is None:
        packages = []
    else:
        packages = dist.packages
    data['packages'] = validate_packages(packages, top)
    if dist.ext_modules:
        data['extensions'] = dict([(e.name, e) for e in dist.ext_modules])
    else:
        data['extensions'] = {}
    data['classifiers'] = dist.get_classifiers()

    data["executables"] = {}

    entry_points = entry_points_from_dist(dist)
    if entry_points:
        console_scripts = entry_points.get("console_scripts", [])
        for entry in console_scripts:
            exe = Executable.from_representation(entry)
            data["executables"][exe.name] = exe

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
    "requires": lambda meta: meta.install_requires,
    "provides": lambda meta: [],
    "obsoletes": lambda meta: []
}

def to_distutils_meta(meta):
    from bento.compat.dist \
        import \
            DistributionMetadata
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

def entry_points_from_dist(dist):
    if hasattr(dist, "entry_points"):
        from pkg_resources import split_sections
        if is_string(dist.entry_points):
            entry_points = {}
            sections = split_sections(dist.entry_points)
            for group, lines in sections:
                group = group.strip()
                entry_points[group] = lines
        else:
            entry_points = dist.entry_points
    else:
        entry_points = {}
    return entry_points
