import sys
import os
import shutil

from bento.installed_package_description \
    import \
        InstalledSection
from bento.errors \
    import \
        CommandExecutionFailure
from bento.utils.utils \
    import \
        cpu_count, extract_exception
import bento.errors

import yaku.task_manager
import yaku.context
import yaku.scheduler
import yaku.errors

def build_extension(bld, extension, env=None):
    builder = bld.builders["pyext"]
    try:
        if env is None:
            env = {"PYEXT_CPPPATH": extension.include_dirs}
        else:
            val = env.get("PYEXT_CPPPATH", [])
            val.extend(extension.include_dirs)
        tasks = builder.extension(extension.name, extension.sources, env)
        if len(tasks) > 1:
            outputs = tasks[0].gen.outputs
        else:
            outputs = []
        return [n.bldpath() for n in outputs]
    except RuntimeError:
        e = extract_exception()
        msg = "Building extension %s failed: %s" % \
              (extension.name, str(e))
        raise CommandExecutionFailure(msg)

def build_compiled_library(bld, clib, env=None):
    builder = bld.builders["ctasks"]
    try:
        for p in clib.include_dirs:
            builder.env["CPPPATH"].insert(0, p)
        outputs = builder.static_library(clib.name, clib.sources, env)
        return [n.bldpath() for n in outputs]
    except RuntimeError:
        e = extract_exception()
        msg = "Building library %s failed: %s" % (clib.name, str(e))
        raise CommandExecutionFailure(msg)
