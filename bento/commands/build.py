import os
import sys

from bento.core.utils import \
        find_package
from bento.installed_package_description import \
        InstalledPkgDescription, InstalledSection, ipkg_meta_from_pkg

from bento.commands.core \
    import \
        Option
from bento.commands \
    import \
        build_distutils
from bento.commands \
    import \
        build_yaku
from bento.commands.core import \
        Command
from bento.commands.configure import \
        get_configured_state
from bento.commands.script_utils import \
        create_posix_script, create_win32_script

class BuildCommand(Command):
    long_descr = """\
Purpose: build the project
Usage:   bentomaker build [OPTIONS]."""
    short_descr = "build the project."
    opts = Command.opts + [
            Option("--use-distutils",
                   help="Use distutils to build extension",
                   action="store_true")]

    def run(self, opts):
        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        if o.use_distutils is None:
            o.use_distutils = True

        if o.use_distutils:
            build_extensions = build_distutils.build_extensions
        else:
            build_extensions = build_yaku.build_extensions

        s = get_configured_state()
        pkg = s.pkg

        section_writer = SectionWriter()
        section_writer.update_sections(pkg)
        section_writer.sections_callbacks["extension"] = \
                build_extensions
        section_writer.store()

class SectionWriter(object):
    def __init__(self):
        self.sections_callbacks = {
            "pythonfiles": build_python_files,
            "datafiles": build_data_files,
            "extension": build_distutils.build_extensions,
            "executable": build_executables
        }
        self.sections = {}
        for k in self.sections_callbacks:
            self.sections[k] = {}

    def update_sections(self, pkg):
        for name, updater in self.sections_callbacks.iteritems():
            self.sections[name].update(updater(pkg))

    def store(self, filename="installed-pkg-info"):
        s = get_configured_state()
        pkg = s.pkg
        scheme = dict([(k, s.paths[k]) for k in s.paths])

        meta = ipkg_meta_from_pkg(pkg)
        p = InstalledPkgDescription(self.sections, meta, scheme,
                                    pkg.executables)
        p.write('installed-pkg-info')

def build_python_files(pkg):
    # FIXME: root_src
    root_src = ""
    python_files = []
    for p in pkg.packages:
        python_files.extend(find_package(p, root_src))
    for m in pkg.py_modules:
        python_files.append(os.path.join(root_src, '%s.py' % m))
    py_section = InstalledSection("pythonfiles", "library",
            root_src, "$sitedir", python_files)

    return {"library": py_section}

def build_data_files(pkg):
    ret = {}
    # Get data files
    for name, data_section in pkg.data_files.items():
        data_section.files = data_section.resolve_glob()
        ret[name] = InstalledSection.from_data_files(name, data_section)

    return ret

def build_dir():
    # FIXME: handle build directory differently, wo depending on distutils
    from distutils.command.build_scripts import build_scripts
    from distutils.dist import Distribution

    dist = Distribution()

    bld_scripts = build_scripts(dist)
    bld_scripts.initialize_options()
    bld_scripts.finalize_options()
    return bld_scripts.build_dir

def build_executables(pkg):
    if not pkg.executables:
        return {}
    bdir = build_dir()
    ret = {}

    for name, executable in pkg.executables.items():
        if sys.platform == "win32":
            ret[name] = create_win32_script(name, executable, bdir)
        else:
            ret[name] = create_posix_script(name, executable, bdir)
    return ret
