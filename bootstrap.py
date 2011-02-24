import sys
import os
import stat

from bento.core \
    import \
        PackageDescription
from bento.core.utils \
    import \
        pprint

from bento.commands.script_utils \
    import \
        create_posix_script, create_win32_script

# We cannot use octal literal for compat with python 3.x
MODE_755 = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | \
    stat.S_IROTH | stat.S_IXOTH

def _create_executable(name, executable):
    if sys.platform == "win32":
        section = create_win32_script(name, executable, ".")
    else:
        section = create_posix_script(name, executable, ".")
        for f, g in section.files:
            os.chmod(g, MODE_755)
    return section

def install_inplace(pkg):
    """Install scripts of pkg in the current directory."""
    for basename, executable in pkg.executables.items():
        version_str = ".".join([str(i) for i in sys.version_info[:2]])
        for name in [basename, "%s-%s" % (basename, version_str)]:
            section = _create_executable(name, executable)
            installed = ",".join([g for f, g in section.files])
            pprint("GREEN", "installing %s in current directory" % installed)

if __name__ == "__main__":
    from setup_common import generate_version_py
    generate_version_py("bento/__dev_version.py")

    pkg = PackageDescription.from_file("bento.info")
    if pkg.executables:
        install_inplace(pkg)
