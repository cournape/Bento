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

def build_extension(bld, pkg, inplace, verbose):
    ret = {}
    all_outputs = {}
    for ext in pkg.extensions.values():
        try:
            if verbose:
                bld.builders["pyext"].env["VERBOSE"] = True
            outputs = bld.builders["pyext"].extension(ext.name, ext.sources)
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
    runner = yaku.scheduler.ParallelRunner(bld, task_manager, cpu_count())
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

def build_extensions(pkg, inplace=False, verbose=False):
    bld = yaku.context.get_bld()

    try:
        return build_extension(bld, pkg, inplace, verbose)
    finally:
        bld.store()
