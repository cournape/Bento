import sys
import os

from bento.core \
    import \
        PackageDescription
from bento.core.utils \
    import \
        pprint

from bento.commands.script_utils \
    import \
        create_posix_script, create_win32_script

def install_inplace(pkg):
    """Install scripts of pkg in the current directory."""
    for name, executable in pkg.executables.items():
        if sys.platform == "win32":
            section = create_win32_script(name, executable, ".")
        else:
            section = create_posix_script(name, executable, ".")
            for f, g in section.files:
                os.chmod(g, 0755)
        installed = ",".join([g for f, g in section.files])
        pprint("GREEN", "installing %s in current directory" % installed)

if __name__ == "__main__":
    from setup_common import generate_version_py
    generate_version_py("bento/__dev_version.py")

    pkg = PackageDescription.from_file("bento.info")
    if pkg.executables:
        install_inplace(pkg)
