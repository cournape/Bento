import sys
import traceback
import optparse

import os.path as op

from six.moves \
    import \
        cStringIO

from bento.utils.utils \
    import \
        pprint, extract_exception, comma_list_split
from bento.core.package \
    import \
        static_representation
from bento.commands.core \
    import \
        Command
from bento.errors \
    import \
        UsageException, ConvertionError
from bento.convert.core \
    import \
        detect_monkeys, monkey_patch, analyse_setup_py, build_pkg
from bento.convert.utils \
    import \
        whole_test

class ConvertCommand(Command):
    long_descr = """\
Purpose: convert a setup.py to an .info file
Usage:   bentomaker convert [OPTIONS] setup.py"""
    short_descr = "convert distutils/setuptools project to bento."
    common_options = Command.common_options + [
        optparse.Option("-t", help="TODO", default="automatic",
               dest="type"),
        optparse.Option("-o", "--output", help="output file",
               default="bento.info",
               dest="output_filename"),
        optparse.Option("-v", "--verbose", help="verbose run",
               action="store_true"),
        optparse.Option("--setup-arguments",
               help="arguments to give to setup" \
                    "For example, --setup-arguments=-q,-n,--with-speedup will " \
                    "call python setup.py -q -n --with-speedup",
               dest="setup_args")]

    def run(self, ctx):
        argv = ctx.command_argv
        p = ctx.options_context.parser
        o, a = p.parse_args(argv)
        if o.help:
            p.print_help()
            return
        if len(a) < 1:
            filename = "setup.py"
        else:
            filename = a[0]
        if not op.exists(filename):
            raise ValueError("file %s not found" % filename)

        output = o.output_filename
        if op.exists(output):
            raise UsageException("file %s exists, not overwritten" % output)

        if o.verbose:
            show_output = True
        else:
            show_output = False

        if o.setup_args:
            setup_args = comma_list_split(o.setup_args)
        else:
            setup_args = ["-q", "-n"]

        monkey_patch_mode = o.type

        convert_log = "convert.log"
        log = open(convert_log, "w")
        try:
            try:
                convert(ctx, filename, setup_args, monkey_patch_mode, o.verbose, output, log, show_output)
            except ConvertionError:
                raise
            except Exception:
                e = extract_exception()
                log.write("Error while converting - traceback:\n")
                tb = sys.exc_info()[2]
                traceback.print_tb(tb, file=log)
                msg = "Error while converting %s - you may look at %s for " \
                      "details (Original exception: %s %s)" 
                raise ConvertionError(msg % (filename, convert_log, type(e), str(e)))
        finally:
            log.flush()
            log.close()

def convert(ctx, filename, setup_args, monkey_patch_mode, verbose, output, log, show_output=True):
    if monkey_patch_mode == "automatic":
        try:
            if verbose:
                pprint("PINK",
                       "Catching monkey (this may take a while) ...")
            monkey_patch_mode = detect_monkeys(filename, show_output, log)
            if verbose:
                pprint("PINK", "Detected mode: %s" % monkey_patch_mode)
        except ValueError:
            e = extract_exception()
            raise UsageException("Error while detecting setup.py type " \
                                 "(original error: %s)" % str(e))

    monkey_patch(ctx.top_node, monkey_patch_mode, filename)
    dist, package_objects = analyse_setup_py(filename, setup_args)
    pkg, options = build_pkg(dist, package_objects, ctx.top_node)

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

class DetectTypeCommand(Command):
    long_descr = """\
Purpose: detect type of distutils extension used by given setup.py
Usage:   bentomaker detect_type [OPTIONS]."""
    short_descr = "detect extension type."
    common_options = Command.common_options + [
        optparse.Option("-i", "--input", help="TODO", default="setup.py", dest="setup_file"),
        optparse.Option("-v", "--verbose", help="verbose run", action="store_true")]

    def run(self, ctx):
        argv = ctx.command_argv
        p = ctx.options_context.parser
        o, a = p.parse_args(argv)
        if o.help:
            p.print_help()
            return
        verbose = o.verbose

        log = cStringIO()

        if verbose:
            print("=================================================================")
            print("Detecting used distutils extension(s) ... (This may take a while)")
        monkey_patch_mode = whole_test(o.setup_file, o.verbose, log)
        if verbose:
            print("Done !")
            print("=================================================================")
        print("Detected type: %r" % monkey_patch_mode)
