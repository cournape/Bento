import os
import os.path as op

from bento.distutils.utils \
    import \
        _is_setuptools_activated
if _is_setuptools_activated():
    from setuptools.command.egg_info \
        import \
            egg_info as old_egg_info
else:
    raise ValueError("You cannot use egg_info without setuptools enabled first")

from bento._config \
    import \
        IPKG_PATH
from bento.installed_package_description \
    import \
        InstalledPkgDescription
from bento.commands.egg_utils \
    import \
        EggInfo

class egg_info(old_egg_info):
    def run(self):
        self.run_command("build")
        dist = self.distribution

        n = dist.build_node.make_node(IPKG_PATH)
        ipkg = InstalledPkgDescription.from_file(n.abspath())

        egg_info = EggInfo.from_ipkg(ipkg, dist.build_node)

        egg_info_dir = op.join(self.egg_base, "%s.egg-info" % dist.pkg.name)
        try:
            os.makedirs(egg_info_dir)
        except OSError, e:
            if e.errno != 17:
                raise
        for filename, cnt in egg_info.iter_meta(dist.build_node):
            filename = op.join(egg_info_dir, filename)
            fid = open(filename, "w")
            try:
                fid.write(cnt)
            finally:
                fid.close()
