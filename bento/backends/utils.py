import sys

import os.path as op

_BACKENDS = {
        "Waf": ("WafBackend", "waf_backend"),
        "Distutils": ("DistutilsBackend", "distutils_backend")
}

def load_backend(backend_name, backend_dirs=None):
    if backend_dirs is None:
        backend_dirs = [op.dirname(__file__)]
    else:
        backend_dirs = [op.dirname(__file__)] + backend_dirs

    if backend_name in _BACKENDS:
        class_name, module_name = _BACKENDS[backend_name]
        sys.path = backend_dirs + sys.path
        try:
            __import__(module_name)
            mod = sys.modules[module_name]
            backend = getattr(mod, class_name, None)
            if backend:
                return backend
            else:
                return ValueError("Backend class %r not found in module %r" % (class_name, mod))
        finally:
            for d in backend_dirs:
                sys.path.remove(d)
    else:
        raise ValueError("Unrecognized backend: %r" % (backend_name,))
