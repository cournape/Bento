import os
import sys

from bento._config \
    import \
        IPKG_PATH
from bento.core.utils \
    import \
        ensure_dir
from bento.core.platforms \
    import \
        get_scheme
from bento.core.meta \
    import \
        PackageMetadata
from bento.installed_package_description \
    import \
        InstalledPkgDescription, iter_files
from bento.commands.install \
    import \
        TransactionLog, rollback_transaction

from bentoshoplib._config \
    import \
        BENTO_HOME, LOG_DIR, BENTO_INSTALL_PREFIX, SCRIPT_NAME
from bentoshoplib.model \
    import \
        init_scheme, PackageIndex

class Command(object):
    pass

def transaction_log(name):
    return os.path.join(LOG_DIR, name[0], name + ".log")

class InitDb(Command):
    def run(self, opts):
        if "-f" in opts:
            force = True
        else:
            force = False
        init_scheme(force=force)

class Install(Command):
    def run(self, opts):
        if not os.path.exists(IPKG_PATH):
            msg = "%s file not found ! (Did you run build ?)" % IPKG_PATH
            raise UsageException(msg)
        package_index = PackageIndex()

        ipkg = InstalledPkgDescription.from_file(IPKG_PATH)
        meta = PackageMetadata.from_ipkg(ipkg)

        ipkg.update_paths(get_scheme(sys.platform)[0])
        prefix = BENTO_INSTALL_PREFIX
        ipkg.update_paths({"prefix": BENTO_INSTALL_PREFIX, "eprefix": BENTO_INSTALL_PREFIX})
        file_sections = ipkg.resolve_paths()

        name = meta.name
        log = transaction_log(name)
        if os.path.exists(log):
            uninstall_package(name)
        ensure_dir(log)

        trans = TransactionLog(log)
        try:
            for kind, source, target in iter_files(file_sections):
                trans.copy(source, target, kind)
        finally:
            trans.close()
        package_index.add_package(meta)

def uninstall_package(name):
    log = os.path.join(LOG_DIR, transaction_log(name))
    if not os.path.exists(log):
        raise IOError("transaction log %s not found: cannot uninstall" % log)
    rollback_transaction(log)

class Uninstall(Command):
    def run(self, opts):
        if len(opts) > 1:
            raise ValueError("uninstall takes a single mandatory argument")
        elif len(opts) < 1:
            # XXX: shall we uninstall the package built in current dir if bento.info ?
            raise ValueError("uninstall takes a single mandatory argument")

        uninstall_package(opts[0])

class List(Command):
    def run(self, opts):
        package_index = PackageIndex()
        for pkg in package_index.list_packages():
            print pkg

class Help(Command):
    def __init__(self, registry):
        Command.__init__(self)
        self.registry = registry

    def run(self):
        print "Usage: %s [CMD]" % SCRIPT_NAME
        print ""
        print "Commands:"
        for cmd_name in self.registry.command_names():
            print "    %s" % cmd_name

class CommandRegistry(object):
    def __init__(self):
        self._registry = {}

    def register_command(self, name,  cmd):
        self._registry[name] = cmd

    def command(self, name):
        ret = self._registry.get(name, None)
        if ret is None:
            raise ValueError("Unregistered command: %s" % name)
        return ret

    def command_names(self):
        return self._registry.keys()
