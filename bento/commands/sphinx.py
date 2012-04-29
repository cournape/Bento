import copy
import os
import subprocess

from bento.commands.core \
    import \
        Command
from bento.commands.options \
    import \
        Option

_OUTPUT_DEFAULT = "html"

# FIXME: where to allow to customize this ?
_DOC_ROOT = "doc"
# relative to _DOC_ROOT
_SOURCE_ROOT = "source"

class SphinxCommand(Command):
    long_descr = """\
Purpose: build sphinx documentation
Usage:   bentomaker sphinx [OPTIONS]."""
    short_descr = "build the project sphinx documentation."
    common_options = Command.common_options + \
                        [Option("--output-format",
                                help="Doc output format (default: %r)" % _OUTPUT_DEFAULT,
                                default=_OUTPUT_DEFAULT)]

    def run(self, context):
        p = context.options_context.parser
        o, a = p.parse_args(context.command_argv)
        if o.output_format != "html":
            raise ValueError("Only html output supported for now")

        doc_node = context.top_node.find_node(_DOC_ROOT)
        if doc_node is None:
            raise IOError("Documentation root %r not found" % _DOC_ROOT)
        doc_root = doc_node.abspath()

        sphinx_build = context.build_node.make_node("sphinx")
        html_build = sphinx_build.make_node("html")
        doctrees_build = sphinx_build.make_node("doctrees")

        doc_html_build = html_build.path_from(doc_node)
        doc_doctrees_build = doctrees_build.path_from(doc_node)

        env = copy.deepcopy(os.environ)
        if "PYTHONPATH" in env:
            env['PYTHONPATH'] = os.pathsep.join(os.getcwd(), env['PYTHONPATH'])
        else:
            env['PYTHONPATH'] = os.getcwd()
        p = subprocess.Popen(["sphinx-build", "-b", "html", "-d", doc_doctrees_build, "source", doc_html_build],
                         cwd=doc_root)
        p.wait()
        if p.returncode != 0:
            raise RuntimeError("error while building doc")
        else:
            print("You can find your HTML doc in %r" % html_build.abspath())
