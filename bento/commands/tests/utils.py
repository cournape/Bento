import os
import sys

if sys.version_info[0] < 3:
    from cStringIO import StringIO
else:
    from io import StringIO


from bento.core \
    import \
        PackageDescription, PackageOptions
from bento.core.package \
    import \
        raw_parse, raw_to_pkg_kw, build_ast_from_raw_dict, PackageDescription
from bento.commands.configure \
    import \
        ConfigureCommand, _setup_options_parser
from bento.commands.build \
    import \
        BuildCommand
from bento.commands.options \
    import \
        OptionsContext
from bento.commands.context \
    import \
        ConfigureYakuContext, BuildYakuContext

class FakeGlobalContext(object):
    def __init__(self):
        self._cmd_opts = {}

    def add_option(self, command_name, option, group=None):
        self._cmd_opts[command_name].add_option(option, group)

def prepare_configure(run_node, bento_info, context_klass=ConfigureYakuContext, cmd_argv=None):
    if cmd_argv is None:
        cmd_argv = []

    top_node = run_node._ctx.srcnode
    top_node.make_node("bento.info").safe_write(bento_info)

    package = PackageDescription.from_string(bento_info)
    package_options = PackageOptions.from_string(bento_info)

    configure = ConfigureCommand()
    opts = OptionsContext.from_command(configure)

    # FIXME: this emulates the big ugly hack inside bentomaker.
    _setup_options_parser(opts, package_options)

    context = context_klass(cmd_argv, opts, package, run_node)
    context.package_options = package_options

    return context, configure

def prepare_options(cmd_name, cmd, context_klass):
    opts = OptionsContext.from_command(cmd)
    g_context = FakeGlobalContext()
    g_context._cmd_opts[cmd_name] = opts
    # FIXME: the way new options are registered for custom contexts sucks:
    # there should be a context class independent way to do it
    if context_klass.__name__ == "BuildWafContext":
        from bento.commands.extras.waf import register_options
        register_options(g_context)
    return opts

def prepare_build(run_node, pkg, context_klass=BuildYakuContext):
    build = BuildCommand()
    opts = prepare_options("build", build, context_klass)

    bld = context_klass([], opts, pkg, run_node)
    return bld, build

# Super ugly stuff to make waf and nose happy: nose happily override
# sys.stdout/sys.stderr, and waf expects real files (with encoding and co). We
# fake it until waf is happy
class EncodedStringIO(object):
    def __init__(self):
        self._data = StringIO()
        self.encoding = "ascii"

    def read(self):
        return self._data.read()

    def write(self, data):
        return self._data.write(data)

