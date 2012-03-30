def is_using_cython(pkg):
    for extension in pkg.extensions.values():
        for source in extension.sources:
            if source.endswith("pyx"):
                return True

    if pkg.subpackages:
        for spkg in pkg.subpackages.values():
            for extension in spkg.extensions.values():
                for source in extension.sources:
                    if source.endswith("pyx"):
                        return True
    return False
