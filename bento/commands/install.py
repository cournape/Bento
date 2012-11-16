import os
import shutil
import subprocess
import errno

from bento._config \
    import \
        BUILD_MANIFEST_PATH
from bento.installed_package_description import \
    BuildManifest, iter_files

from bento.commands.core import \
    Command, Option
from bento.utils.utils import \
    pprint, extract_exception, MODE_755, MODE_777

def _rollback_operation(line):
    operation, arg = line.split()
    if operation == "MKDIR":
        try:
            os.rmdir(arg)
        except OSError:
            e = extract_exception()
            # FIXME: hardcoded errno !!
            if e.errno != 66:
                raise
    elif operation == "COPY":
        os.remove(arg)
    else:
        raise ValueError("Unknown operation: %s" % operation)

def rollback_transaction(f):
    fid = open(f)
    try:
        lines = fid.readlines()
        for i in range(len(lines)-1, -1, -1):
            _rollback_operation(lines[i])
            lines.pop(i)
    finally:
        fid.close()
        if len(lines) < 1:
            os.remove(f)
        else:
            fid = open(f, "w")
            try:
                fid.writelines(lines)
            finally:
                fid.close()

class TransactionLog(object):
    """Naive version of a journal to rollback interrupted install."""
    def __init__(self, journal_filename):
        if os.path.exists(journal_filename):
            raise IOError("file %s already exists" % journal_filename)
        open(journal_filename, "w").close()
        self.f = open(journal_filename, "w")
        self.journal_filename = journal_filename

    def copy(self, source, target, category):
        if os.path.exists(target):
            self.rollback()
            raise ValueError("File %s already exists, rolled back installation" % target)
        d = os.path.dirname(target)
        if not os.path.exists(d):
            self.makedirs(d)
        self.f.write("COPY %s\n" % target)
        shutil.copy(source, target)
        if category == "executables":
            os.chmod(target, MODE_755)

    def makedirs(self, name, mode=MODE_777):
        head, tail = os.path.split(name)
        if not tail:
            head, tail = os.path.split(head)
        if head and tail and not os.path.exists(head):
            try:
                self.makedirs(head, mode)
            except OSError:
                e = extract_exception()
                if e.errno != errno.EEXIST:
                    raise
            if tail == os.curdir:
                return
        self.mkdir(name, mode)

    def mkdir(self, name, mode=MODE_777):
        self.f.write("MKDIR %s\n" % name) 
        self.f.flush()
        os.mkdir(name, mode)

    def close(self):
        if self.f is not None:
            self.f.close()

    def rollback(self):
        self.f.close()
        self.f = open(self.journal_filename, "r")
        lines = self.f.readlines()
        for line in lines[::-1]:
            _rollback_operation(line.strip())
        self.f = None

def copy_installer(source, target, kind):
    dtarget = os.path.dirname(target)
    if not os.path.exists(dtarget):
        os.makedirs(dtarget)
    shutil.copy(source, target)
    if kind == "executables":
        os.chmod(target, MODE_755)

def unix_installer(source, target, kind):
    if kind in ["executables"]:
        mode = "755"
    else:
        mode = "644"
    cmd = ["install", "-m", mode, source, target]
    strcmd = "INSTALL %s -> %s" % (source, target)
    pprint('GREEN', strcmd)
    if not os.path.exists(os.path.dirname(target)):
        os.makedirs(os.path.dirname(target))
    subprocess.check_call(cmd)

class InstallCommand(Command):
    long_descr = """\
Purpose: install the project
Usage:   bentomaker install [OPTIONS]."""
    short_descr = "install the project."
    common_options = Command.common_options + \
                        [Option("-t", "--transaction",
                                help="Do a transaction-based install", action="store_true"),
                         Option("-n", "--dry-run", "--list-files",
                                help="List installed files (do not install anything)",
                                action="store_true", dest="list_files")]
    def run(self, ctx):
        argv = ctx.command_argv
        p = ctx.options_context.parser
        o, a = p.parse_args(argv)
        if o.help:
            p.print_help()
            return

        n = ctx.build_node.make_node(BUILD_MANIFEST_PATH)
        build_manifest = BuildManifest.from_file(n.abspath())
        scheme = ctx.retrieve_configured_scheme()
        build_manifest.update_paths(scheme)
        node_sections = build_manifest.resolve_paths_with_destdir(ctx.build_node)

        if o.list_files:
            # XXX: this won't take into account action in post install scripts.
            # A better way would be to log install steps and display those, but
            # this will do for now.
            for kind, source, target in iter_files(node_sections):
                print(target.abspath())
            return

        if o.transaction:
            trans = TransactionLog("transaction.log")
            try:
                for kind, source, target in iter_files(node_sections):
                    trans.copy(source.abspath(), target.abspath(), kind)
            finally:
                trans.close()
        else:
            for kind, source, target in iter_files(node_sections):
                copy_installer(source.abspath(), target.abspath(), kind)
