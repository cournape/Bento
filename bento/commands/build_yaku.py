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

import yaku.task_manager
import yaku.context
import yaku.scheduler
import yaku.errors

def build_isection(bld, ext_name, files):
    # Given an extension name and the list of files which constitute
    # it (e.g. the .so on unix, the .pyd on windows, etc...), return
    # an InstallSection

    # FIXME: do package -> location translation correctly
    pkg_dir = os.path.dirname(ext_name.replace('.', os.path.sep))
    target = os.path.join('$sitedir', pkg_dir)

    # FIXME: assume all outputs of one extension are in one directory
    srcdir = files[0].parent.path_from(bld.src_root)
    section = InstalledSection("extensions", ext_name, srcdir,
                                target, [o.name for o in files])
    return section

def build_extension(bld, extension, verbose):
    builder = bld.builders["pyext"]
    try:
        if verbose:
            builder.env["VERBOSE"] = True
        return builder.extension(extension.name, extension.sources)
    except RuntimeError, e:
        msg = "Building extension %s failed: %s" % \
              (extension.name, str(e))
        raise CommandExecutionFailure(msg)

def _build_extensions(bld, pkg, inplace, verbose):
    ret = {}
    if len(pkg.extensions) < 1:
        return  ret

    all_outputs = {}
    for ext in pkg.extensions.values():
        outputs = build_extension(bld, ext, verbose)
        ret[ext.name] = build_isection(bld, ext.name, outputs)

    task_manager = yaku.task_manager.TaskManager(bld.tasks)
    runner = yaku.scheduler.SerialRunner(bld, task_manager)
    runner.start()
    runner.run()

    if inplace:
        so_ext = bld.builders["pyext"].env["PYEXT_SO"]
        # FIXME: do package -> location + remove hardcoded extension
        # FIXME: handle in-place at yaku level
        for ext, outputs in all_outputs.items():
            for o in outputs:
                target = os.path.join(
                            os.path.dirname(ext.replace(".", os.sep)),
                            os.path.basename(o.abspath()))
                shutil.copy(o.abspath(), target)
    return ret

def build_compiled_library(bld, pkg, inplace, verbose):
    ret = {}
    if len(pkg.compiled_libraries) < 1:
        return  ret

    all_outputs = {}
    for ext in pkg.compiled_libraries.values():
        builder = bld.builders["ctasks"]
        try:
            if verbose:
                builder.env["VERBOSE"] = True
            for p in ext.include_dirs:
                builder.env["CPPPATH"].insert(0, p)
            outputs = builder.static_library(ext.name, ext.sources)
            all_outputs[ext.name] = outputs
        except RuntimeError, e:
            msg = "Building extension %s failed: %s" % (ext.name, str(e))
            raise CommandExecutionFailure(msg)

        # FIXME: do package -> location translation correctly
        pkg_dir = os.path.dirname(ext.name.replace('.', os.path.sep))
        target = os.path.join('$sitedir', pkg_dir)
        fullname = ext.name
        ext_targets = outputs
        # FIXME: assume all outputs of one extension are in one directory
        srcdir = os.path.dirname(ext_targets[0])
        section = InstalledSection("extensions", fullname, srcdir,
                                    target, [os.path.basename(o) for o in outputs])
        ret[fullname] = section

    task_manager = yaku.task_manager.TaskManager(bld.tasks)
    runner = yaku.scheduler.SerialRunner(bld, task_manager)
    runner.start()
    runner.run()

    if inplace:
        so_ext = bld.builders["pyext"].env["PYEXT_SO"]
        # FIXME: do package -> location + remove hardcoded extension
        # FIXME: handle in-place at yaku level
        for ext, outputs in all_outputs.items():
            for o in outputs:
                target = os.path.join(
                            os.path.dirname(ext.replace(".", os.sep)),
                            os.path.basename(o))
                shutil.copy(o, target)
    return ret

import bento.core.errors

def build_extensions(ctx, pkg, inplace=False, verbose=False):
    bld = ctx.yaku_build_ctx
    try:
        return _build_extensions(bld, pkg, inplace, verbose)
    except yaku.errors.TaskRunFailure, e:
        if e.explain:
            msg = e.explain
        else:
            msg = ""
        msg += "command '%s' failed (see above)" % " ".join(e.cmd)
        raise bento.core.errors.BuildError(msg)

def build_compiled_libraries(ctx, pkg, inplace=False, verbose=False):
    bld = ctx.yaku_build_ctx
    try:
        return build_compiled_library(bld, pkg, inplace, verbose)
    except yaku.errors.TaskRunFailure, e:
        if e.explain:
            msg = e.explain
        else:
            msg = ""
        msg += "command '%s' failed (see above)" % " ".join(e.cmd)
        raise bento.core.errors.BuildError(msg)
