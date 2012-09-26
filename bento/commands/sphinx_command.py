import copy
import os
import subprocess
import sys

import os.path as op

import bento.errors

from bento.commands.core \
    import \
        Command
from bento.commands.options \
    import \
        Option
from bento.utils.utils \
    import \
        extract_exception

_OUTPUT_DEFAULT = "html"

# FIXME: where to allow to customize this ?
_DOC_ROOT = "doc"
# relative to _DOC_ROOT
_SOURCE_ROOT = "source"

def guess_source_dir():
    for guess in ('doc', 'docs'):
        if not op.isdir(guess):
            continue
        for root, dirnames, filenames in os.walk(guess):
            if 'conf.py' in filenames:
                return root
    return None

class SphinxCommand(Command):
    long_descr = """\
Purpose: build sphinx documentation
Usage:   bentomaker sphinx [OPTIONS]."""
    short_descr = "build the project sphinx documentation."
    common_options = Command.common_options + \
                        [Option("--output-format",
                                help="Doc output format (default: %r)" % _OUTPUT_DEFAULT,
                                default=_OUTPUT_DEFAULT),
                         Option("--source-dir",
                             help="Doc source directory (guessed if not specified)"),
                         Option("--config-dir",
                             help="Config directory (guessed if not specified)"),
                         ]

    def can_run(self):
        try:
            import sphinx.application
            return True
        except ImportError:
            return False
        except SyntaxError:
            return False

    def run(self, context):
        if not self.can_run():
            return bento.errors.CommandExecutionFailure("sphinx not available")
        import sphinx.application

        p = context.options_context.parser
        o, a = p.parse_args(context.command_argv)
        if o.output_format != "html":
            raise ValueError("Only html output supported for now")
        else:
            builder = "html"

        if o.source_dir is None:
            source_dir = guess_source_dir()
        else:
            source_dir = o.source_dir
        if source_dir is None:
            raise bento.errors.UsageException("""\
Doc source dir could not be found: please specify the directory where your
sphinx conf.py is located with the --source-dir option""")
        if not op.isabs(source_dir):
            source_dir = op.join(context.top_node.abspath(), source_dir)

        sphinx_build = context.build_node.make_node("sphinx")
        html_build = sphinx_build.make_node(o.output_format)
        doctrees_build = sphinx_build.make_node("doctrees")

        doc_html_build = html_build.abspath()
        doc_doctrees_build = doctrees_build.abspath()

        confoverrides = {}
        status_stream = sys.stdout
        fresh_env = False
        force_all = False

        app = sphinx.application.Sphinx(
                source_dir, source_dir,
                doc_html_build, doc_doctrees_build,
                builder, confoverrides, status_stream,
                freshenv=fresh_env)
        try:
            app.build(force_all=force_all)
        except Exception:
            err = extract_exception()
            raise bento.errors.CommandExecutionFailure("error while building doc: %r" % str(err))
