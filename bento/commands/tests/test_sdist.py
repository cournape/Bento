import os
import os.path as op
import unittest
import tempfile
import shutil
import zipfile

from bento.core.package \
    import \
        PackageDescription
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.commands.options \
    import \
        OptionsContext
from bento.commands.cmd_contexts \
    import \
        SdistContext
from bento.commands.sdist \
    import \
        SdistCommand
from bento.core.testing \
    import \
        create_fake_package_from_bento_infos, create_fake_package_from_bento_info

class TestBaseSdist(unittest.TestCase):
    def setUp(self):
        self.save = os.getcwd()
        self.d = tempfile.mkdtemp()
        os.chdir(self.d)
        try:
            self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))
            self.top_node = self.root._ctx.srcnode
            self.build_node = self.root._ctx.bldnode
            self.run_node = self.root.find_node(self.d)
        except Exception:
            os.chdir(self.save)
            raise

    def tearDown(self):
        os.chdir(self.save)
        shutil.rmtree(self.d)

    def test_simple_package(self):
        bento_info = """\
Name: foo
Version: 1.0

ExtraSourceFiles: yeah.info

Library:
    Packages: foo, foo.bar
    Modules: fubar
"""
        archive_list = [op.join("foo-1.0", f) for f in ["yeah.info",
                                                        op.join("foo", "__init__.py"),
                                                        op.join("foo", "bar", "__init__.py"),
                                                        "fubar.py"]]

        create_fake_package_from_bento_info(self.top_node, bento_info)
        package = PackageDescription.from_string(bento_info)

        sdist = SdistCommand()
        opts = OptionsContext.from_command(sdist)
        cmd_argv = ["--output-file=foo.zip", "--format=zip"]

        context = SdistContext(None, cmd_argv, opts, package, self.run_node)
        sdist.run(context)
        sdist.shutdown(context)
        context.shutdown()

        archive = self.run_node.find_node(op.join("dist", "foo.zip"))
        z = zipfile.ZipFile(archive.abspath(), "r")
        for f in archive_list:
            if not f in z.namelist():
                self.failUnless(op.join("foo-1.0", f) in files)

    def test_extra_source_registration(self):
        bento_info = """\
Name: foo
Version: 1.0

Library:
    Modules: fubar
"""
        archive_list = [op.join("foo-1.0", f) for f in ["fubar.py", "yeah.info"]]

        extra_node = self.top_node.make_node("yeah.info")
        extra_node.write("")

        create_fake_package_from_bento_info(self.top_node, bento_info)
        package = PackageDescription.from_string(bento_info)

        sdist = SdistCommand()
        opts = OptionsContext.from_command(sdist)
        cmd_argv = ["--output-file=foo.zip", "--format=zip"]

        context = SdistContext(None, cmd_argv, opts, package, self.run_node)
        context.register_source_node(self.top_node.find_node("yeah.info"))
        sdist.run(context)
        sdist.shutdown(context)
        context.shutdown()

        archive = self.run_node.find_node(op.join("dist", "foo.zip"))
        z = zipfile.ZipFile(archive.abspath(), "r")
        for f in archive_list:
            if not f in z.namelist():
                self.failUnless(op.join("foo-1.0", f) in files)

    def test_extra_source_with_alias(self):
        bento_info = """\
Name: foo
Version: 1.0

Library:
    Modules: fubar
"""
        archive_list = [op.join("foo-1.0", f) for f in ["fubar.py", "bohou.info"]]

        extra_node = self.top_node.make_node("yeah.info")
        extra_node.write("")

        create_fake_package_from_bento_info(self.top_node, bento_info)
        package = PackageDescription.from_string(bento_info)

        sdist = SdistCommand()
        opts = OptionsContext.from_command(sdist)
        cmd_argv = ["--output-file=foo.zip", "--format=zip"]

        context = SdistContext(None, cmd_argv, opts, package, self.run_node)
        context.register_source_node(self.top_node.find_node("yeah.info"), archive_name="bohou.info")
        sdist.run(context)
        sdist.shutdown(context)
        context.shutdown()

        archive = self.run_node.find_node(op.join("dist", "foo.zip"))
        z = zipfile.ZipFile(archive.abspath(), "r")
        for f in archive_list:
            if not f in z.namelist():
                self.failUnless(op.join("foo-1.0", f) in files)

    def test_template_filling(self):
        bento_info = """\
Name: foo
Version: 1.0

MetaTemplateFile: release.py.in

Library:
    Modules: fubar
"""
        archive_list = [op.join("foo-1.0", f) for f in ["fubar.py", "release.py.in", "release.py"]]

        template = self.top_node.make_node("release.py.in")
        template.write("""\
NAME = $NAME
VERSION = $VERSION
""")

        create_fake_package_from_bento_info(self.top_node, bento_info)
        package = PackageDescription.from_string(bento_info)

        sdist = SdistCommand()
        opts = OptionsContext.from_command(sdist)
        cmd_argv = ["--output-file=foo.zip", "--format=zip"]

        context = SdistContext(None, cmd_argv, opts, package, self.run_node)
        sdist.run(context)
        sdist.shutdown(context)
        context.shutdown()

        archive = self.run_node.find_node(op.join("dist", "foo.zip"))
        z = zipfile.ZipFile(archive.abspath(), "r")
        for f in archive_list:
            if not f in z.namelist():
                self.fail("File %s not found in archive" % (f,))
