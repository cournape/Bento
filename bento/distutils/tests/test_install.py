import os.path as op

from bento.distutils.tests.common \
    import \
        DistutilsCommandTestBase
from bento.distutils.dist \
    import \
        BentoDistribution
from bento.distutils.commands.install \
    import \
        install
        
class TestInstallCommand(DistutilsCommandTestBase):
    def test_simple(self):
        fid = open(op.join(self.new_cwd, "bento.info"), "wt")
        try:
            fid.write("""\
Name: foo
""")
        finally:
            fid.close()

        dist = BentoDistribution()
        cmd = install(dist)

        install_dir = op.join(self.new_cwd, "install")
        cmd.prefix = install_dir
        cmd.dry_run = True
        cmd.record = op.join(self.new_cwd, "record.txt")
        cmd.ensure_finalized()

        cmd.run()
