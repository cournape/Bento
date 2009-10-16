from toydist.package import \
        PackageDescription

def distutils_to_package_description(dist):
    name = dist.get_name()
    version = dist.get_version()
    py_modules = dist.py_modules
    packages = dist.packages

    return PackageDescription(name, version=version, py_modules=py_modules,
            packages=packages)
