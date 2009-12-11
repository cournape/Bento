from toydist.package import \
        PackageDescription

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

    return PackageDescription(**data)
