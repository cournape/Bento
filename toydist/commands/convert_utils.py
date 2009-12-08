import os
import sys
import tempfile

from subprocess import \
        PIPE, Popen, call, STDOUT

from toydist.utils import \
        pprint

distutils_code = """\
import sys
import distutils.core

from distutils.core import setup as _setup

DIST = None

def new_setup(**kw):
    global DIST
    dist = _setup(**kw)
    DIST = dist
    return dist

filename = '%(filename)s'

globals = {}
globals["__name__"] = "__main__"
globals["__file__"] = filename

sys.argv = [filename, "config"]
distutils.core.setup = new_setup
execfile(filename, globals)

if DIST is None:
    sys.exit(-2)

if DIST.__module__ == "distutils.dist":
    sys.exit(0)
else:
    sys.exit(-1)
"""

setuptools_code = """\
import sys
import setuptools
import distutils.core

from setuptools import setup as _setup

DIST = None

def new_setup(**kw):
    global DIST
    dist = _setup(**kw)
    DIST = dist
    return dist

filename = '%(filename)s'

globals = {}
globals["__name__"] = "__main__"
globals["__file__"] = filename

sys.argv = [filename, "-q", "--help"]
setuptools.setup = new_setup
execfile(filename, globals)
print DIST.__module__

if DIST is None:
    sys.exit(-2)

if DIST.__module__ == "setuptools.dist":
    sys.exit(0)
else:
    sys.exit(-1)
"""

numpy_code = """\
import sys
try:
    import numpy.distutils.core
    from numpy.distutils.core import setup as _setup

    DIST = None

    def new_setup(**kw):
        global DIST
        dist = _setup(**kw)
        DIST = dist
        return dist

    filename = '%(filename)s'

    globals = {}
    globals["__name__"] = "__main__"
    globals["__file__"] = filename

    sys.argv = [filename, "-q", "--name"]
    numpy.distutils.core.setup = new_setup
    execfile(filename, globals)

    print DIST
    if DIST is None:
        sys.exit(-2)

    if DIST.__module__ == "numpy.distutils.numpy_distribution":
        sys.exit(0)
    else:
        sys.exit(-1)
except ImportError, e:
    print e
    sys.exit(-1)
"""

setuptools_numpy_code = """\
import sys
try:
    import numpy.distutils.core
    from numpy.distutils.core import setup as _setup

    DIST = None

    def new_setup(**kw):
        global DIST
        dist = _setup(**kw)
        DIST = dist
        return dist

    filename = '%(filename)s'

    globals = {}
    globals["__name__"] = "__main__"
    globals["__file__"] = filename

    sys.argv = [filename, "-q", "--name"]
    numpy.distutils.core.setup = new_setup
    execfile(filename, globals)

    if DIST is None:
        sys.exit(-2)

    if DIST.__module__ == "numpy.distutils.numpy_distribution" and \\
        "setuptools" in sys.modules:
        sys.exit(0)
    else:
        sys.exit(-1)
except ImportError:
    sys.exit(-1)
"""

can_run_code = """\
import sys

filename = '%(filename)s'

globals = {}
globals["__name__"] = "__main__"
globals["__file__"] = filename

sys.argv = [filename, "-q", "--name"]
execfile(filename, globals)
"""

def _test(code, setup_py, show_output=False):
    fake_out, filename_out = tempfile.mkstemp(suffix=".out", text=True)
    try:
        fid, filename = tempfile.mkstemp(suffix=".py", text=True)
        try:
            os.write(fid, code)
            if show_output:
                return call([sys.executable, filename]) == 0
            else:
                return call([sys.executable, filename], stdout=fake_out,
                            stderr=PIPE) == 0
        finally:
            os.close(fid)
            os.remove(filename)
    finally:
        os.close(fake_out)
        os.remove(filename_out)

def test_distutils(setup_py, show_output):
    return _test(distutils_code % {"filename": setup_py}, setup_py,
                 show_output)

def test_setuptools(setup_py, show_output):
    return _test(setuptools_code % {"filename": setup_py}, setup_py,
                 show_output)

def test_numpy(setup_py, show_output):
    return _test(numpy_code % {"filename": setup_py}, setup_py, show_output)

def test_setuptools_numpy(setup_py, show_output):
    return _test(setuptools_numpy_code % {"filename": setup_py}, setup_py,
                 show_output)

def test_can_run(setup_py, show_output):
    return _test(can_run_code % {"filename": setup_py}, setup_py, show_output)

def whole_test(setup_py, verbose=True):
    if verbose:
        show_output = True
    else:
        show_output = False

    if not test_can_run(setup_py, show_output):
        pass
    pprint("YELLOW", "----------------- Testing distutils ------------------")
    use_distutils = test_distutils(setup_py, show_output)
    pprint("YELLOW", "----------------- Testing setuptools -----------------")
    use_setuptools = test_setuptools(setup_py, show_output)
    pprint("YELLOW", "------------ Testing numpy.distutils -----------------")
    use_numpy = test_numpy(setup_py, show_output)
    pprint("YELLOW", "--- Testing numpy.distutils patched by setuptools ----")
    use_setuptools_numpy = test_setuptools_numpy(setup_py, show_output)
    if verbose:
        print "Is distutils ?", use_distutils
        print "Is setuptools ?", use_setuptools
        print "Is numpy distutils ?", use_numpy
        print "Is setuptools numpy ?", use_setuptools_numpy

    if use_distutils and not (use_setuptools or use_numpy or use_setuptools_numpy):
        return "distutils converter"
    elif use_setuptools  and not (use_numpy or use_setuptools_numpy):
        return "setuptools converter"
    elif use_numpy  and not use_setuptools_numpy:
        return "numpy.distutils converter"
    elif use_setuptools_numpy:
        return "setuptools + numpy.distutils converter"
    else:
        return "Unsupported converter"

if __name__ == "__main__":
    setup_py = sys.argv[1]
