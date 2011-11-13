import os.path as op

from bento.distutils.tests.common \
    import \
        DistutilsCommandTestBase
from bento.distutils.dist \
    import \
        BentoDistribution
from bento.distutils.commands.sdist \
    import \
        sdist
        
class TestSdistCommand(DistutilsCommandTestBase):
    def test_simple(self):
        fid = open(op.join(self.new_cwd, "bento.info"), "wt")
        try:
            fid.write("""\
Name: foo
""")
        finally:
            fid.close()

        dist = BentoDistribution()
        cmd = sdist(dist)

        cmd.ensure_finalized()

        cmd.run()
