def has_cython_code(pkg):
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

def has_compiled_code(pkg):
    has_compiled_code = len(pkg.extensions) > 0 or len(pkg.compiled_libraries) > 0
    if not has_compiled_code:
        if pkg.subpackages:
            for v in pkg.subpackages.values():
                if len(v.extensions) > 0 or len(v.compiled_libraries) > 0:
                    has_compiled_code = True
                    break
    return has_compiled_code
