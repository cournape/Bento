import sys
import os

from bento.core \
    import \
        PackageDescription
from bento.utils.utils \
    import \
        pprint, MODE_755

from bento.core.node \
    import \
        create_root_with_source_tree
from bento.commands.script_utils \
    import \
        create_posix_script, create_win32_script

root = create_root_with_source_tree(os.getcwd(), os.path.join(os.getcwd(), "build"))

def _create_executable(name, executable, scripts_node):
    if sys.platform == "win32":
        nodes = create_win32_script(name, executable, scripts_node)
    else:
        nodes = create_posix_script(name, executable, scripts_node)
        for n in nodes:
            n.chmod(MODE_755)
    return nodes

def install_inplace(pkg):
    """Install scripts of pkg in the current directory."""
    for basename, executable in pkg.executables.items():
        version_str = ".".join([str(i) for i in sys.version_info[:2]])
        scripts_node = root._ctx.srcnode
        for name in [basename, "%s-%s" % (basename, version_str)]:
            nodes = _create_executable(name, executable, scripts_node)
            installed = ",".join([n.path_from(scripts_node) for n in nodes])
            pprint("GREEN", "installing %s in current directory" % installed)

def main():
    pkg = PackageDescription.from_file("bento.info")
    if pkg.executables:
        install_inplace(pkg)

if __name__ == "__main__":
    main()
