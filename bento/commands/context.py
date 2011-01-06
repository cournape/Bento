import os
import sys
import cPickle

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

import yaku.context

from bento.core.package_cache \
    import \
        CachedPackage
from bento.commands.configure \
    import \
        get_configured_state
from bento._config \
    import \
        ARGS_CHECKSUM_DB_FILE

class CmdContext(object):
    def __init__(self, cmd, cmd_argv, pkg, top_node):
        self.pkg = pkg
        self.cmd = cmd
        # FIXME: ugly hack to get help option - think about option handling
        # interaction between bentomaker and bento commands
        if cmd.parser is not None:
            o, a = cmd.parser.parse_args(cmd_argv)
            self.help = o.help
        else:
            self.help = False

        self.cmd_argv = cmd_argv
        self.top_node = top_node

    def get_command_arguments(self):
        return self.cmd_argv

    def get_package(self):
        state = get_configured_state()
        return state.pkg

    def get_user_data(self):
        state = get_configured_state()
        return state.user_data

    def store(self):
        pass

class ConfigureContext(CmdContext):
    def __init__(self, cmd, cmd_argv, pkg, top_node):
        CmdContext.__init__(self, cmd, cmd_argv, pkg, top_node)
        self.yaku_configure_ctx = yaku.context.get_cfg()

    def store(self):
        CmdContext.store(self)
        self.yaku_configure_ctx.store()
        CachedPackage.write_checksums()
        _write_argv_checksum(_argv_checksum(sys.argv), "configure")

class BuildContext(CmdContext):
    def __init__(self, cmd, cmd_argv, pkg, top_node):
        CmdContext.__init__(self, cmd, cmd_argv, pkg, top_node)
        self.yaku_build_ctx = yaku.context.get_bld()
        self._extensions_callback = {}
        self._clibraries_callback = {}
        self._clibrary_envs = {}
        self._extension_envs = {}

    def store(self):
        CmdContext.store(self)
        self.yaku_build_ctx.store()

        checksum = _read_argv_checksum("configure")
        _write_argv_checksum(checksum, "build")

    def _compute_extension_name(self, extension_name):
        if self.local_node ==  self.top_node:
            relpos = ""
        else:
            relpos = self.local_node.path_from(self.top_node)
        extension = relpos.replace(os.path.pathsep, ".")
        if extension:
            full_name = extension + ".%s" % extension_name
        else:
            full_name = extension_name
        return full_name

    # XXX: none of those register_* really belong here
    def register_builder(self, extension_name, builder):
        full_name = self._compute_extension_name(extension_name)
        self._extensions_callback[full_name] = builder

    def register_clib_builder(self, clib_name, builder):
        relpos = self.local_node.path_from(self.top_node)
        full_name = os.path.join(relpos, clib_name)
        self._clibraries_callback[full_name] = builder

    def register_environment(self, extension_name, env):
        full_name = self._compute_extension_name(extension_name)
        self._extension_envs[full_name] = env

    def register_clib_environment(self, clib_name, env):
        relpos = self.local_node.path_from(self.top_node)
        full_name = os.path.join(relpos, clib_name)
        self._clibrary_envs[full_name] = env

def _argv_checksum(argv):
    return md5(cPickle.dumps(argv)).hexdigest()

def _read_argv_checksum(cmd_name):
    fid = open(ARGS_CHECKSUM_DB_FILE, "rb")
    try:
        data = cPickle.load(fid)
        return data[cmd_name]
    finally:
        fid.close()

def _write_argv_checksum(checksum, cmd_name):
    if os.path.exists(ARGS_CHECKSUM_DB_FILE):
        fid = open(ARGS_CHECKSUM_DB_FILE, "rb")
        try:
            data = cPickle.load(fid)
        finally:
            fid.close()
    else:
        data = {}

    data[cmd_name] = checksum
    fid = open(ARGS_CHECKSUM_DB_FILE, "wb")
    try:
        cPickle.dump(data, fid)
    finally:
        fid.close()
