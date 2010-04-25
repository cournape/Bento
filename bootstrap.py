import sys
import os

from toydist.core \
    import \
        PackageDescription
from toydist.core.utils \
    import \
        pprint

from toydist.commands.script_utils \
    import \
        create_posix_script, create_win32_script

def install_inplace(pkg):
    """Install scripts of pkg in the current directory."""
    for name, executable in pkg.executables.items():
        if sys.platform == "win32":
            section = create_win32_script(name, executable, ".")
        else:
            section = create_posix_script(name, executable, ".")
            for f in section.files:
                os.chmod(f, 0755)
        installed = ",".join(section.files)
        pprint("GREEN", "installing %s in current directory" % installed)

if __name__ == "__main__":
    from setup_common import generate_version_py
    generate_version_py("toydist/__dev_version.py")

    pkg = PackageDescription.from_file("toysetup.info")
    if pkg.executables:
        install_inplace(pkg)
