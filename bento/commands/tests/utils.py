import os.path as op

from six.moves \
    import \
        StringIO

from bento.backends.yaku_backend \
    import \
        ConfigureYakuContext, BuildYakuContext, YakuBackend
from bento.commands.build \
    import \
        BuildCommand
from bento.commands.configure \
    import \
        ConfigureCommand
from bento.commands.contexts \
    import \
        GlobalContext
from bento.commands.options \
    import \
        OptionsContext
from bento.core \
    import \
        PackageDescription, PackageOptions
from bento.core.testing \
    import \
        create_fake_package_from_bento_info

def prepare_configure(run_node, bento_info, context_klass=ConfigureYakuContext, cmd_argv=None):
    if cmd_argv is None:
        cmd_argv = []
    return _prepare_command(run_node, bento_info, ConfigureCommand, context_klass, cmd_argv)

def prepare_build(run_node, bento_info, context_klass=BuildYakuContext, cmd_argv=None):
    if cmd_argv is None:
        cmd_argv = []
    return _prepare_command(run_node, bento_info, BuildCommand, context_klass, cmd_argv)

def _prepare_command(run_node, bento_info, cmd_klass, context_klass, cmd_argv):
    top_node = run_node._ctx.srcnode
    top_node.make_node("bento.info").safe_write(bento_info)

    package = PackageDescription.from_string(bento_info)
    package_options = PackageOptions.from_string(bento_info)

    cmd = cmd_klass()
    options_context = OptionsContext.from_command(cmd)

    cmd.register_options(options_context, package_options)

    global_context = GlobalContext(None)
    global_context.register_package_options(package_options)

    context = context_klass(global_context, cmd_argv, options_context, package, run_node)
    return context, cmd

def create_global_context(package, package_options, backend=None):
    if backend is None:
        backend = YakuBackend()

    global_context = GlobalContext(None)
    global_context.register_package_options(package_options)
    if backend:
        global_context.backend = backend

    build = BuildCommand()
    configure = ConfigureCommand()

    commands = (("configure", configure), ("build", build))

    for cmd_name, cmd in commands:
        global_context.register_command(cmd_name, cmd)
        options_context = OptionsContext.from_command(cmd)
        global_context.register_options_context(cmd_name, options_context)

    global_context.backend.register_command_contexts(global_context)
    global_context.backend.register_options_contexts(global_context)

    return global_context

def prepare_package(top_node, bento_info, backend=None):
    package = PackageDescription.from_string(bento_info)
    package_options = PackageOptions.from_string(bento_info)

    create_fake_package_from_bento_info(top_node, bento_info)
    top_node.make_node("bento.info").safe_write(bento_info)

    return create_global_context(package, package_options, backend)

def prepare_command(global_context, cmd_name, cmd_argv, package, run_node):
    if cmd_argv is None:
        cmd_argv = []

    def _create_context(cmd_name):
        context_klass = global_context.retrieve_command_context(cmd_name)
        options_context = global_context.retrieve_options_context(cmd_name)
        context = context_klass(global_context, cmd_argv, options_context, package, run_node)
        return context

    return _create_context(cmd_name), global_context.retrieve_command(cmd_name)

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

    def flush(self):
        self._data.flush()

def comparable_installed_sections(sections):
    # Hack to compare compiled sections without having to hardcode the exact,
    # platform-dependent name
    class _InstalledSectionProxy(object):
        def __init__(self, installed_section):
            self.installed_section = installed_section

        def __eq__(self, other):
            _self = self.installed_section
            _other = other.installed_section
            def are_files_comparables():
                if len(_self.files) != len(_other.files):
                    return False
                else:
                    for i in range(len(_self.files)):
                        for j in range(2):
                            if op.dirname(_self.files[i][j]) != \
                                    op.dirname(_other.files[i][j]):
                                return False
                    return True

            return _self.name == _other.name and \
                _self.source_dir == _other.source_dir and \
                _self.target_dir == _other.target_dir and \
                are_files_comparables()

        def __repr__(self):
            return self.installed_section.__repr__()

    def proxy_categories(sections):
        for category in sections:
            for section_name, section in sections[category].items():
                sections[category ][section_name] = _InstalledSectionProxy(section)
        return sections

    return proxy_categories(sections)
