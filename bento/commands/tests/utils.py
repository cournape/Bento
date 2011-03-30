from bento._config \
    import \
        BUILD_DIR
from bento.core \
    import \
        PackageDescription, PackageOptions
from bento.commands.configure \
    import \
        ConfigureCommand, _setup_options_parser
from bento.commands.options \
    import \
        OptionsContext
from bento.commands.context \
    import \
        ConfigureYakuContext

def prepare_configure(top_node, bento_info, context_klass=ConfigureYakuContext):
    # FIXME: this should be created in the configure context
    junk_node = top_node.make_node(BUILD_DIR)
    junk_node.mkdir()

    package = PackageDescription.from_string(bento_info)
    package_options = PackageOptions.from_string(bento_info)

    configure = ConfigureCommand()
    opts = OptionsContext()
    for o in ConfigureCommand.common_options:
        opts.add_option(o)
    context = context_klass(configure, [], opts, package, top_node)

    # FIXME: this emulates the big ugly hack inside bentomaker.
    _setup_options_parser(opts, package_options)
    context.package_options = package_options

    return context, configure

