import os
import sys
import warnings
import posixpath
import ntpath

import os.path as op

from bento.conv \
    import \
        find_package, distutils_to_package_description
from bento.core.utils \
    import \
        pprint, extract_exception
from bento.core.pkg_objects \
    import \
        PathOption, DataFiles

from bento.commands.errors \
    import \
        UsageException, ConvertionError

class SetupCannotRun(Exception):
    pass

# ====================================================
# Code to convert existing setup.py to bento.info
# ====================================================
LIVE_OBJECTS = {}
def _process_data_files(seq):
    ret = {}
    for name, data in seq.iteritems():
        ndots = name.count(".")
        if ndots > 0:
            pdir = op.join(*[os.pardir for i in range(ndots)])
        else:
            pdir = ""
        ret[name] = [op.join(pdir, f) for f in data]
    return ret

# XXX: this is where the magic happens. This is highly dependent on the
# setup.py, whether it uses distutils, numpy.distutils, setuptools and whatnot.
def monkey_patch(type, filename):
    supported = ["distutils", "numpy_distutils", "setuptools", "setuptools_numpy"]

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
    elif type == "numpy_distutils":
        import numpy.distutils
        import distutils.core
        from numpy.distutils.core import setup as old_setup
        from numpy.distutils.command.build_py import build_py as old_build_py
        from numpy.distutils.command.sdist import sdist as old_sdist
        from numpy.distutils.numpy_distribution import NumpyDistribution as _Distribution
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
                _build_py.run(self)
                # package_data: data files which correspond to packages (and
                # are installed)

                # setuptools has its own logic to deal with package_data, and
                # do so in build_py
                if type == "setuptools":
                    LIVE_OBJECTS["package_data"] = _process_data_files(self.distribution.package_data)
                else:
                    LIVE_OBJECTS["package_data"] = {}
                _build_py.run(self)

                # extra_data
                LIVE_OBJECTS["extra_data"] = get_data_files()

                # Those are directly created from setup data_files argument
                LIVE_OBJECTS["dist_data_files"] = self.distribution.data_files
                # those are created from package_data stuff
                LIVE_OBJECTS["data_files"] = self.data_files

        cmdclass["build_py"] = build_py_recorder
        kw["cmdclass"] = cmdclass

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
    elif type == "numpy_distutils":
        numpy.distutils.core.setup = new_setup
        distutils.core.setup = new_setup
    else:
        raise UsageException("Unknown converter: %s (known converters are %s)" % 
                         (type, ", ".join(supported)))

def analyse_setup_py(filename, setup_args, verbose=False):
    if verbose:
        pprint('PINK', "======================================================")
        pprint('PINK', " Analysing %s (running %s) .... " % (filename, filename))

    # exec_globals contains the globals used to execute the setup.py
    exec_globals = {}
    exec_globals.update(globals())
    # Some setup.py files call setup from their main, so execute them as if
    # they were the main script
    exec_globals["__name__"] = "__main__"
    exec_globals["__file__"] = op.abspath(filename)

    _saved_argv = sys.argv[:]
    _saved_sys_path = sys.path
    try:
        try:
            sys.argv = [filename] + setup_args + ["build_py"]
            # XXX: many packages import themselves to get version at build
            # time, and setuptools screw this up by inserting stuff first. Is
            # there a better way ?
            sys.path.insert(0, op.dirname(filename))
            execfile(filename, exec_globals)
            if type == "distutils" and "setuptools" in sys.modules and verbose:
                pprint("YELLOW", "Setuptools detected in distutils mode !!!")
        except Exception:
            e = extract_exception()
            pprint('RED', "Got exception: %s" % e)
            raise e
    finally:
        sys.argv = _saved_argv
        sys.path = _saved_sys_path

    if not "dist" in LIVE_OBJECTS:
        raise ValueError("setup monkey-patching failed")
    dist = LIVE_OBJECTS["dist"]

    if verbose:
        pprint('PINK', " %s analyse done " % filename)
        pprint('PINK', "======================================================")

    return dist

def build_pkg(dist, live_objects, top_node):
    if dist.package_dir is not None:
        for package, path in dist.package_dir.iteritems():
            if not op.samefile(package.replace(".", os.sep), path):
                raise ConvertionError("setup.py with package_dir arguments is not supported (was %r)." % dist.package_dir)

    pkg = distutils_to_package_description(dist)
    modules = []
    for m in pkg.py_modules:
        if isinstance(m, basestring):
            modules.append(m)
        else:
            warnings.warn("The module %s it not understood" % str(m))
    pkg.py_modules = modules

    path_options = []
    pkg.data_files = {}
    if live_objects["package_data"]:
        gendatafiles = {}
        for package, files in live_objects["package_data"].iteritems():
            if len(files) > 0:
                # FIXME: use nodes here instead of ugly path manipulations
                name = "gendata_%s" % package.replace(".", "_")
                target_dir = op.join("$gendatadir", package.replace(".", "/"))
                data_section = DataFiles(name, files, target_dir)
                pkg.data_files[name] = data_section
        path_options.append(PathOption("gendatadir", "$sitedir",
                "Directory for datafiles obtained from distutils conversion"
                ))

    extra_source_files = []
    if live_objects["extra_data"]:
        extra_source_files.extend([canonalize_path(f) 
                                  for f in live_objects["extra_data"]])
    pkg.extra_source_files = sorted(prune_extra_files(extra_source_files, pkg, top_node))

    if live_objects["data_files"]:
        data_files = live_objects["data_files"]
        for pkg_name, source_dir, _, files in data_files:
            if len(files) > 0:
                name = "%s_data" % pkg_name.replace(".", "_")
                target_dir = op.join("$sitedir", pkg_name.replace(".", os.sep))
                pkg.data_files[name] = DataFiles(name, files, target_dir, source_dir)

    if dist.scripts:
        name = "%s_scripts" % pkg.name
        target_dir = "$eprefix"
        pkg.data_files[name] = DataFiles(name, dist.scripts, target_dir, ".")

    # numpy.distutils bug: packages are appended twice to the Distribution
    # instance, so we prune the list here
    pkg.packages = sorted(list(set(pkg.packages)))
    options = {"path_options": path_options}
    
    return pkg, options

def prune_extra_files(files, pkg, top_node):

    package_files = []
    for p in pkg.packages:
        package_files.extend(find_package(p, top_node))

    data_files = []
    for data_section in pkg.data_files.values():
        data_files.extend([op.join(data_section.source_dir, f) for f in data_section.files])

    redundant = package_files + data_files + pkg.py_modules

    return prune_file_list(files, redundant)

def detect_monkeys(setup_py, show_output, log):
    from bento.convert.utils import \
        test_distutils, test_setuptools, test_numpy, test_setuptools_numpy, \
        test_can_run

    if not test_can_run(setup_py, show_output, log):
        raise SetupCannotRun()

    def print_delim(string):
        if show_output:
            pprint("YELLOW", string)

    print_delim("----------------- Testing distutils ------------------")
    use_distutils = test_distutils(setup_py, show_output, log)
    print_delim("----------------- Testing setuptools -----------------")
    use_setuptools = test_setuptools(setup_py, show_output, log)
    print_delim("------------ Testing numpy.distutils -----------------")
    use_numpy = test_numpy(setup_py, show_output, log)
    print_delim("--- Testing numpy.distutils patched by setuptools ----")
    use_setuptools_numpy = test_setuptools_numpy(setup_py, show_output, log)
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

# Functions below should always produce posix-style paths, even on windows
def combine_groups(data_files):
    """Given a list of tuple (target, files), combine files together per
    target/srcdir.
    
    Example
    -------
    
    data_files = [('foo', ['src/file1', 'src/file2'])]
    
    combine_groups returns:
        {'foo_src': {
            'target': 'foo',
            'srcdir': 'src',
            'files':
                ['file1', 'file2']}
        }.
    """

    ret = {}
    for data_file in data_files:
        # FIXME: install policies should not be handled here
        # FIXME: find the cases when entries' length are 2 vs 3 vs 4
        if len(data_file) == 2:
            target = posixpath.join("$sitedir", data_file[0])
            sources = data_file[1]
        elif len(data_file) == 3:
            target = posixpath.join("$prefix", data_file[1])
            sources = data_file[2]
        else:
            raise NotImplementedError("data files with >3 components not handled yet")

        for source in sources:
            srcdir = op.dirname(source)
            name = canonalize_path(op.basename(source))

            # Generate a unique key for target/source combination
            key = "%s_%s" % (target.replace(op.sep, "_"), srcdir.replace(op.sep, "_"))
            if ret.has_key(key):
                if not (ret[key]["srcdir"] == srcdir and ret[key]["target"] == target):
                    raise ValueError("BUG: mismatch for key %s ?" % key)
                ret[key]["files"].append(name)
            else:
                d = {}
                d["srcdir"] = srcdir
                d["target"] = target
                d["files"] = [name]
                ret[key] = d

    return ret

def prune_file_list(files, redundant):
    """Prune a list of files relatively to a second list.

    Return a subsequence of `files' which contains only files not in
    `redundant'

    Parameters
    ----------
    files: seq
        list of files to prune.
    redundant: seq
        list of candidate files to prune.
    """
    files_set = set([posixpath.normpath(f) for f in files if not isinstance(f, basestring)])
    redundant_set = set([posixpath.normpath(f) for f in redundant if not isinstance(f, basestring)])

    return list(files_set.difference(redundant_set))

def canonalize_path(path):
    """Convert a win32 path to unix path."""
    if op.sep == "/":
        return path
    head, tail = ntpath.split(path)
    lst = [tail]
    while head and tail:
        head, tail = ntpath.split(head)
        lst.insert(0, tail)
    lst.insert(0, head)

    return posixpath.join(*lst)
