import os
import sys
import tempfile

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from subprocess import \
        PIPE, call, STDOUT, Popen

from bento.core.utils import \
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
sys.path.insert(0, '%(odir)s')
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
distutils.core.setup = new_setup
sys.path.insert(0, '%(odir)s')
execfile(filename, globals)

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
    sys.path.insert(0, '%(odir)s')
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
    import setuptools
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
    sys.path.insert(0, '%(odir)s')
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
sys.path.insert(0, '%(odir)s')
execfile(filename, globals)
"""

def logged_run(cmd, buffer):
    """Return exit code."""
    pid = Popen(cmd, stdout=PIPE, stderr=STDOUT)
    pid.wait()

    buffer.write(pid.stdout.read())
    return pid.returncode
    
def _test(code, setup_py, show_output, log):
    fid, filename = tempfile.mkstemp(suffix=".py", text=True)
    try:
        cmd = [sys.executable, filename]
        log.write(" | Running %s, content below\n" % " ".join(cmd))
        log.writelines([" | | %s\n" % line for line in code.splitlines()])

        os.write(fid, code)

        buf = StringIO()
        st = logged_run(cmd, buf)

        # FIXME: handle this correctly
        log.write(" | return of the command is %d and output is\n" % st)
        val = buf.getvalue()
        if val:
            log.writelines([" | | %s\n" % line for line in val.splitlines()])
            log.write("\n")
        else:
            log.write(" | (None)\n")
        log.write("\n")
        return st == 0
    finally:
        os.close(fid)
        os.remove(filename)

def test_distutils(setup_py, show_output, log):
    odir = os.path.dirname(os.path.abspath(setup_py))
    log.write("bentomaker: convert\n")
    log.write(" -> testing straight distutils\n")
    return _test(distutils_code % {"filename": setup_py, "odir": odir}, setup_py,
                 show_output, log)

def test_setuptools(setup_py, show_output, log):
    odir = os.path.dirname(os.path.abspath(setup_py))
    log.write("bentomaker: convert\n")
    log.write(" -> testing setuptools\n")
    return _test(setuptools_code % {"filename": setup_py, "odir": odir}, setup_py,
                 show_output, log)

def test_numpy(setup_py, show_output, log):
    odir = os.path.dirname(os.path.abspath(setup_py))
    log.write("bentomaker: convert\n")
    log.write(" -> testing straight numpy.distutils\n")
    return _test(numpy_code % {"filename": setup_py, "odir": odir}, setup_py,
                 show_output, log)

def test_setuptools_numpy(setup_py, show_output, log):
    odir = os.path.dirname(os.path.abspath(setup_py))
    log.write("bentomaker: convert\n")
    log.write(" -> testing numpy.distutils monkey-patched by setuptools\n")
    return _test(setuptools_numpy_code % {"filename": setup_py, "odir": odir}, setup_py,
                 show_output, log)

def test_can_run(setup_py, show_output, log):
    odir = os.path.dirname(os.path.abspath(setup_py))
    log.write("bentomaker: convert\n")
    log.write(" -> testing whether setup.py can be executed without errors\n")
    return _test(can_run_code % {"filename": setup_py, "odir": odir}, setup_py,
                 show_output, log)

def whole_test(setup_py, verbose, log):
    if verbose:
        show_output = True
    else:
        show_output = False

    if not test_can_run(setup_py, show_output, log):
        pass
    pprint("YELLOW", "----------------- Testing distutils ------------------")
    use_distutils = test_distutils(setup_py, show_output, log)
    pprint("YELLOW", "----------------- Testing setuptools -----------------")
    use_setuptools = test_setuptools(setup_py, show_output, log)
    pprint("YELLOW", "------------ Testing numpy.distutils -----------------")
    use_numpy = test_numpy(setup_py, show_output, log)
    pprint("YELLOW", "--- Testing numpy.distutils patched by setuptools ----")
    use_setuptools_numpy = test_setuptools_numpy(setup_py, show_output, log)
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
