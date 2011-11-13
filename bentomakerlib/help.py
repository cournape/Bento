import bento

from bento.commands.core \
    import \
        USAGE, fill_string

def get_usage(global_context):
    ret = [USAGE % {"name": "bentomaker",
                    "version": bento.__version__}]
    ret.append("Bento commands:")

    commands = []
    cmd_names = sorted(global_context.command_names())
    for name in cmd_names:
        v = global_context.retrieve_command(name)
        doc = v.short_descr
        if doc is None:
            doc = "undocumented"
        header = "  %s" % name
        commands.append((header, doc))

    minlen = max([len(header) for header, hlp in commands]) + 2
    for header, hlp in commands:
        ret.append(fill_string(header, minlen) + hlp)
    return "\n".join(ret)

