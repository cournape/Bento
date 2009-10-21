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

    data['install_requires'] = dist.install_requires

    data['py_modules'] = dist.py_modules
    data['packages'] = dist.packages
    data['extensions'] = dist.ext_modules

    return PackageDescription(**data)
