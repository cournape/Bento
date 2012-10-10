import os.path as op

from bento.distutils.tests.common \
    import \
        DistutilsCommandTestBase

import bento.core.testing

class TestEggInfoCommand(DistutilsCommandTestBase):
    @bento.core.testing.skip_if(True)
    def test_simple(self):
        from bento.distutils.dist \
            import \
                BentoDistribution
        from bento.distutils.commands.egg_info \
            import \
                egg_info

        fid = open(op.join(self.new_cwd, "bento.info"), "wt")
        try:
            fid.write("""\
Name: foo
""")
        finally:
            fid.close()

        dist = BentoDistribution()
        cmd = egg_info(dist)

        cmd.ensure_finalized()

        cmd.run()
