import os.path as op

from bento.distutils.tests.common \
    import \
        DistutilsCommandTestBase
from bento.distutils.dist \
    import \
        BentoDistribution
from bento.distutils.commands.build \
    import \
        build
        
class TestBuildCommand(DistutilsCommandTestBase):
    def test_hook(self):
        "Test hook is executed at all in distutils compat mode."
        fid = open(op.join(self.new_cwd, "bento.info"), "wt")
        try:
            fid.write("""\
Name: foo
HookFile: bscript
""")
        finally:
            fid.close()

        fid = open(op.join(self.new_cwd, "bscript"), "wt")
        try:
            fid.write("""\
from bento.commands import hooks

@hooks.pre_build
def pre_build(context):
    raise ValueError()
""")
        finally:
            fid.close()

        dist = BentoDistribution()
        cmd = build(dist)
        cmd.ensure_finalized()
        self.assertRaises(ValueError, cmd.run)
