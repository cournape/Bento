import sys
import os
import shutil

from bento.installed_package_description \
    import \
        InstalledSection
from bento.commands.errors \
    import \
        CommandExecutionFailure
from bento.core.utils \
    import \
        cpu_count
import bento.core.errors

import yaku.task_manager
import yaku.context
import yaku.scheduler
import yaku.errors

def build_isection(bld, ext_name, files, category):
    # FIXME: use bento nodes, not yaku...
    # TODO: make this function common between all builders (distutils, yaku, etc...)
    if len(files) < 1:
        return InstalledSection.from_source_target_directories(category, ext_name,
            "", "", files)
    # Given an extension name and the list of files which constitute
    # it (e.g. the .so on unix, the .pyd on windows, etc...), return
    # an InstallSection

    # FIXME: do package -> location translation correctly
    pkg_dir = os.path.dirname(ext_name.replace('.', os.path.sep))
    target = os.path.join('$sitedir', pkg_dir)

    # FIXME: assume all outputs of one extension are in one directory
    srcdir = files[0].parent.path_from(bld.src_root)
    section = InstalledSection.from_source_target_directories("extensions", ext_name, srcdir,
                                target, [o.name for o in files])
    return section

def build_extension(bld, extension, verbose, env=None):
    builder = bld.builders["pyext"]
    try:
        if verbose:
            builder.env["VERBOSE"] = True
        if env is None:
            env = {"PYEXT_CPPPATH": extension.include_dirs}
        else:
            val = env.get("PYEXT_CPPPATH", [])
            val.extend(extension.include_dirs)
        return builder.extension(extension.name, extension.sources,
                                 env)
    except RuntimeError, e:
        msg = "Building extension %s failed: %s" % \
              (extension.name, str(e))
        raise CommandExecutionFailure(msg)

def build_compiled_library(bld, clib, verbose, env=None):
    builder = bld.builders["ctasks"]
    try:
        if verbose:
            builder.env["VERBOSE"] = True
        for p in clib.include_dirs:
            builder.env["CPPPATH"].insert(0, p)
        return builder.static_library(clib.name, clib.sources, env)
    except RuntimeError, e:
        msg = "Building library %s failed: %s" % (clib.name, str(e))
        raise CommandExecutionFailure(msg)
