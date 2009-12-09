import os
import sys

from toydist.utils import \
        pprint, find_package, prune_file_list
from toydist.package import \
        static_representation
from toydist.conv import \
        distutils_to_package_description
from toydist.cabal_parser.items import \
        FlagOption

from toydist.commands.core import \
        Command, UsageException

# ====================================================
# Code to convert existing setup.py to toysetup.info
# ====================================================
LIVE_OBJECTS = {}
def _process_data_files(seq):
    ret = []
    for i in seq:
        # FIXME: use package_dir to translate package to path
        target = i[0].replace(".", os.path.sep)
        srcdir = i[1]
        ret.append({"files": i[3], "srcdir": srcdir, "target": target})
    return ret

# XXX: this is where the magic happens. This is highly dependent on the
# setup.py, whether it uses distutils, numpy.distutils, setuptools and whatnot.
def monkey_patch(type, filename):
    supported = ["distutils", "setuptools", "setuptools_numpy"]

    if type == "distutils":
        from distutils.core import setup as old_setup
        from distutils.command.build_py import build_py as old_build_py
        from distutils.command.sdist import sdist as old_sdist
        from distutils.dist import Distribution as _Distribution
        from distutils.filelist import FileList
    elif type == "setuptools":
        from setuptools import setup as old_setup
        from setuptools.command.build_py import build_py as old_build_py
        from setuptools.command.sdist import sdist as old_sdist
        from distutils.dist import Distribution as _Distribution
        from distutils.filelist import FileList
    elif type == "setuptools_numpy":
        import setuptools
        import numpy.distutils
        import distutils.core
        from numpy.distutils.core import setup as old_setup
        from numpy.distutils.command.build_py import build_py as old_build_py
        from numpy.distutils.command.sdist import sdist as old_sdist
        from numpy.distutils.numpy_distribution import NumpyDistribution as _Distribution
        from distutils.filelist import FileList
    else:
        raise UsageException("Unknown converter: %s (known converters are %s)" % 
                         (type, ", ".join(supported)))

    def get_data_files():
        # FIXME: handle redundancies between data files, package data files
        # (i.e. installed data files) and files included as part of modules,
        # packages, extensions, .... Given the giant mess that distutils makes
        # of things here, it may not be possible to get everything right,
        # though.
        dist = _Distribution()
        sdist = old_sdist(dist)
        sdist.initialize_options()
        sdist.finalize_options()
        sdist.manifest_only = True
        sdist.filelist = FileList()
        sdist.distribution.script_name = filename
        sdist.get_file_list()
        return sdist.filelist.files


    def new_setup(**kw):
        cmdclass = kw.get("cmdclass", {})
        try:
            _build_py = cmdclass["build_py"]
        except KeyError:
            _build_py = old_build_py

        class build_py_recorder(_build_py):
            def run(self):
                if type == "setuptools":
                    LIVE_OBJECTS["package_data"] = _process_data_files(self._get_data_files())
                else:
                    LIVE_OBJECTS["package_data"] = []
                _build_py.run(self)

                LIVE_OBJECTS["extra_data"] = get_data_files()

        cmdclass["build_py"] = build_py_recorder
        kw["cmdclass"] = cmdclass

        #if type == "setuptools_numpy":
        #    # XXX: Remove configuration to avoid executing the setup twice in
        #    # numpy.distutils (see setup code in numpy.distutils.core)
        #    if kw.has_key("configuration"):
        #        kw.pop("configuration")

        dist = old_setup(**kw)
        LIVE_OBJECTS["dist"] = dist
        return dist

    if type == "distutils":
        import distutils.core
        distutils.core.setup = new_setup
    elif type == "setuptools":
        import distutils.core
        import setuptools
        distutils.core.setup = new_setup
        setuptools.setup = new_setup
    elif type == "setuptools_numpy":
        numpy.distutils.core.setup = new_setup
        setuptools.setup = new_setup
        distutils.core.setup = new_setup
    else:
        raise UsageException("Unknown converter: %s (known converters are %s)" % 
                         (type, ", ".join(supported)))

class ConvertCommand(Command):
    long_descr = """\
Purpose: convert a setup.py to an .info file
Usage:   toymaker convert [OPTIONS] setup.py"""
    short_descr = "convert the project to toydist."
    opts = Command.opts + [
        {"opts": ["-t"], "help": "TODO", "default": "automatic", "dest": "type"},
        {"opts": ["-o", "--output"], "help": "output file", "default": "toysetup.info",
                  "dest": "output_filename"},
        {"opts": ["-v", "--verbose"], "help": "verbose run", "action" : "store_true"},
    ]

    def run(self, opts):
        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        if len(a) < 1:
            raise UsageException("convert command requires an argument.")
        filename = a[0]
        if not os.path.exists(filename):
            raise ValueError("file %s not found" % filename)

        output = o.output_filename
        if os.path.exists(output):
            raise UsageException("file %s exists, not overwritten" % output)

        if o.verbose:
            show_output = True
        else:
            show_output = False

        tp = o.type
        if tp == "automatic":
            try:
                pprint("PINK",
                       "Detecting monkey patches (this may take a while) ...")
                tp = detect_monkeys(filename, show_output)
                pprint("PINK", "Detected mode: %s" % tp)
            except ValueError, e:
                raise UsageException("Error while detecting setup.py type " \
                                     "(original error: %s)" % str(e))

        monkey_patch(tp, filename)

        pprint('PINK', "======================================================")
        pprint('PINK', " Analysing %s (running %s) .... " % (filename, filename))

        # exec_globals contains the globals used to execute the setup.py
        exec_globals = {}
        exec_globals.update(globals())
        # Some setup.py files call setup from their main, so execute them as if
        # they were the main script
        exec_globals["__name__"] = "__main__"
        exec_globals["__file__"] = os.path.abspath(filename)

        _saved_argv = sys.argv[:]
        try:
            sys.argv = [filename, "-q", "-n", "build_py"]
            execfile(filename, exec_globals)
            if type == "distutils" and "setuptools" in sys.modules:
                pprint("YELLOW", "Setuptools detected in distutils mode !!!")
        except Exception, e:
            pprint('RED', "Got exception: %s" % e)
            raise e
        finally:
            sys.path = _saved_argv

        if not "dist" in LIVE_OBJECTS:
            raise ValueError("setup monkey-patching failed")
        dist = LIVE_OBJECTS["dist"]

        pprint('PINK', " %s analyse done " % filename)
        pprint('PINK', "======================================================")

        pkg = distutils_to_package_description(dist)
        path_options = []
        pkg.data_files = {}
        if LIVE_OBJECTS["package_data"]:
            gendatafiles = {}
            for d in LIVE_OBJECTS["package_data"]:
                if len(d["files"]) > 0:
                    name = "gendata_%s" % d["target"].replace(os.path.sep, "_")
                    gendatafiles[name] = {
                        "srcdir": d["srcdir"],
                        "target": os.path.join("$gendatadir", d["target"]),
                        "files": d["files"]
                    }
            path_options.append(FlagOption("gendatadir", "$sitedir",
                    "Directory for datafiles obtained from distutils conversion"
                    ))
            pkg.data_files.update(gendatafiles)

        extra_source_files = []
        if LIVE_OBJECTS["extra_data"]:
            extra_source_files.extend(LIVE_OBJECTS["extra_data"])
        pkg.extra_source_files = sorted(prune_extra_files(extra_source_files, pkg))

        options = {"path_options": path_options}
        out = static_representation(pkg, options)

        if output == '-':
            for line in out.splitlines():
                pprint("YELLOW", line)
        else:
            fid = open(output, "w")
            try:
                fid.write(out)
            finally:
                fid.close()

def prune_extra_files(files, pkg):

    package_files = []
    for p in pkg.packages:
        package_files.extend(find_package(p))

    data_files = []
    for sec in pkg.data_files:
        srcdir_field = pkg.data_files[sec]['srcdir']
        files_field = pkg.data_files[sec]['files']
        data_files.extend([os.path.join(srcdir_field, f) for f in files_field])

    redundant = package_files + data_files + pkg.py_modules

    return prune_file_list(files, redundant)

def detect_monkeys(setup_py, show_output):
    from toydist.commands.convert_utils import \
        test_distutils, test_setuptools, test_numpy, test_setuptools_numpy, \
        test_can_run

    if not test_can_run(setup_py, show_output):
        raise  SetupCannotRun()

    def print_delim(string):
        if show_output:
            pprint("YELLOW", string)

    print_delim("----------------- Testing distutils ------------------")
    use_distutils = test_distutils(setup_py, show_output)
    print_delim("----------------- Testing setuptools -----------------")
    use_setuptools = test_setuptools(setup_py, show_output)
    print_delim("------------ Testing numpy.distutils -----------------")
    use_numpy = test_numpy(setup_py, show_output)
    print_delim("--- Testing numpy.distutils patched by setuptools ----")
    use_setuptools_numpy = test_setuptools_numpy(setup_py, show_output)
    print_delim("Is distutils ? %s" % use_distutils)
    print_delim("Is setuptools ? %s" % use_setuptools)
    print_delim("Is numpy distutils ? %s" % use_numpy)
    print_delim("Is setuptools numpy ? %s" % use_setuptools_numpy)

    if use_distutils and not (use_setuptools or use_numpy or use_setuptools_numpy):
        return "distutils"
    elif use_setuptools  and not (use_numpy or use_setuptools_numpy):
        return "setuptools"
    elif use_numpy  and not use_setuptools_numpy:
        return "numpy"
    elif use_setuptools_numpy:
        return "setuptools_numpy"
    else:
        raise ValueError("Unsupported converter")
