import os
import sys

from toydist.utils import \
        pprint
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
        source = i[1]
        ret.append({"files": i[3], "source": source, "target": target})
    return ret

# XXX: this is where the magic happens. This is highly dependent on the
# setup.py, whether it uses distutils, numpy.distutils, setuptools and whatnot.
def monkey_patch(type):
    supported = ["distutils", "setuptools", "setuptools_numpy"]
    
    if type == "distutils":
        from distutils.core import setup as old_setup
        from distutils.command.build_py import build_py as old_build_py
    elif type == "setuptools":
        from setuptools import setup as old_setup
        from setuptools.command.build_py import build_py as old_build_py
    elif type == "setuptools_numpy":
        import setuptools
        import numpy.distutils
        import distutils.core
        from numpy.distutils.core import setup as old_setup
        from numpy.distutils.command.build_py import build_py as old_build_py
    else:
        raise UsageException("Unknown converter: %s (known converters are %s)" % 
                         (type, ", ".join(supported)))

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
        {"opts": ["-t"], "help": "TODO", "default": "distutils", "dest": "type"},
        {"opts": ["-o", "--output"], "help": "output file", "default": "toysetup.info",
                  "dest": "output_filename"},
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

        tp = o.type
        monkey_patch(tp)

        pprint('PINK', "======================================================")
        pprint('PINK', " Analysing %s (running %s) .... " % (filename, filename))
        _saved_argv = sys.argv[:]
        try:
            sys.argv = [filename, "-q", "-n", "build_py"]
            execfile(filename, globals())
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
                        "source": d["source"],
                        "target": os.path.join("$gendatadir", d["target"]),
                        "files": d["files"]
                    }
            path_options.append(FlagOption("gendatadir", "$sitedir",
                    "Directory for datafiles obtained from distutils conversion"
                    ))
            pkg.data_files.update(gendatafiles)

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

