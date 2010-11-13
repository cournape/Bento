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

def run_tasks(bld, all_outputs, inplace, jobs):
    task_manager = yaku.task_manager.TaskManager(bld.tasks)
    if jobs is None:
        runner = yaku.scheduler.SerialRunner(bld, task_manager)
    else:
        runner = yaku.scheduler.ParallelRunner(bld, task_manager, jobs)
    runner.start()
    runner.run()

    if inplace:
        # FIXME: do package -> location + remove hardcoded extension
        # FIXME: handle in-place at yaku level
        for ext, outputs in all_outputs.items():
            for o in outputs:
                target = os.path.join(
                            os.path.dirname(ext.replace(".", os.sep)),
                            os.path.basename(o.abspath()))
                shutil.copy(o.abspath(), target)
    return

def build_isection(bld, ext_name, files):
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

def _build_extensions(extensions, bld, environments, inplace, verbose,
        extension_callback, jobs):
    ret = {}
    if len(extensions) < 1:
        return  ret

    all_outputs = {}
    subexts = {}

    for name, ext in extensions.items():
        env = environments.get(name, None)
        if name in extension_callback:
            tasks = extension_callback[name](bld, ext, verbose)
            if tasks is None:
                raise ValueError(
                    "Registered callback for %s did not return " \
                    "a list of tasks!" % ext.name)
        else:
            tasks = build_extension(bld, ext, verbose, env)
        if len(tasks) > 1:
            outputs = tasks[0].gen.outputs
            if len(outputs) > 0:
                all_outputs[ext.name] = outputs
                ret[ext.name] = build_isection(bld, ext.name, outputs)

    run_tasks(bld, all_outputs, inplace, jobs)
    return ret

def build_compiled_library(bld, clib, verbose, callbacks, env=None):
    builder = bld.builders["ctasks"]
    try:
        if verbose:
            builder.env["VERBOSE"] = True
        for p in clib.include_dirs:
            builder.env["CPPPATH"].insert(0, p)
        if clib.name in callbacks:
            tasks = callbacks[clib.name](bld, clib, verbose)
            if tasks is None:
                raise ValueError(
                    "Registered callback for %s did not return " \
                    "a list of tasks!" % clib.name)
        else:
            tasks = builder.static_library(clib.name, clib.sources,
                                           env)
        return tasks
    except RuntimeError, e:
        msg = "Building library %s failed: %s" % (clib.name, str(e))
        raise CommandExecutionFailure(msg)

def _build_compiled_libraries(compiled_libraries, bld, environments,
        inplace, verbose, callbacks, jobs):
    ret = {}
    if len(compiled_libraries) < 1:
        return  ret

    all_outputs = {}
    for clib in compiled_libraries.values():
        env = environments.get(clib.name, None)
        outputs = build_compiled_library(bld, clib,
                                         verbose, callbacks, env)
        all_outputs[clib.name] = outputs
        ret[clib.name] = build_isection(bld, clib.name, outputs)

    run_tasks(bld, all_outputs, inplace, jobs)
    return ret

def build_extensions(extensions, yaku_build_ctx, builder_callbacks,
        environments, inplace=False, verbose=False, jobs=None):
    try:
        return _build_extensions(extensions, yaku_build_ctx,
                environments, inplace, verbose, builder_callbacks, jobs)
    except yaku.errors.TaskRunFailure, e:
        if e.explain:
            msg = e.explain.encode("utf-8")
        else:
            msg = ""
        msg += "command '%s' failed (see above)" % " ".join(e.cmd)
        raise bento.core.errors.BuildError(msg)

def build_compiled_libraries(libraries, yaku_build_ctx, callbacks,
        environments, inplace=False, verbose=False, jobs=None):
    try:
        return _build_compiled_libraries(libraries, yaku_build_ctx,
                environments, inplace, verbose, callbacks, jobs)
    except yaku.errors.TaskRunFailure, e:
        if e.explain:
            msg = e.explain.encode("utf-8")
        else:
            msg = ""
        msg += "command '%s' failed (see above)" % " ".join(e.cmd)
        raise bento.core.errors.BuildError(msg)
