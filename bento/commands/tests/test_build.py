import os
import shutil
import unittest
import tempfile

import nose

from nose.plugins.skip \
    import \
        SkipTest

from bento.core.node \
    import \
        create_root_with_source_tree
from bento.core \
    import \
        PackageDescription
from bento.commands.context \
    import \
        BuildContext, BuildYakuContext, ConfigureYakuContext, DistutilsBuildContext, DistutilsConfigureContext
from bento.commands.options \
    import \
        OptionsContext, Option
from bento.commands.build \
    import \
        BuildCommand
from bento.installed_package_description \
    import \
        InstalledSection

import bento.commands.build_distutils
import bento.commands.build_yaku

from yaku.context \
    import \
        get_bld, get_cfg

from bento.commands.tests.utils \
    import \
        prepare_configure, create_fake_package, create_fake_package_from_bento_infos, \
        prepare_build, create_fake_package_from_bento_info

BENTO_INFO_WITH_EXT = """\
Name: foo

Library:
    Extension: foo
        Sources: foo.c
"""

BENTO_INFO = """\
Name: foo

Library:
    Packages: foo, foo.bar
    Modules: fubar
"""

def skipif(condition, msg=None):
    def skip_decorator(f):
        if callable(condition):
            skip_func = condition
        else:
            skip_func = lambda : condition()

        if skip_func():
            def g(*a, **kw):
                raise SkipTest()
        else:
            g = f
        return nose.tools.make_decorator(f)(g)
    return skip_decorator

class _TestBuildSimpleExtension(unittest.TestCase):
    def setUp(self):
        self.save = None
        self.d = None

        self.save = os.getcwd()
        self.d = tempfile.mkdtemp()

        os.chdir(self.d)

        self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))

        # Those should be set by subclasses
        self._configure_context = None
        self._build_context = None
        self._dummy_builder = None

    def tearDown(self):
        if self.save:
            os.chdir(self.save)
        if self.d:
            shutil.rmtree(self.d)

    def test_no_extension(self):
        top_node = self.root.srcnode

        create_fake_package_from_bento_infos(top_node, {"bento.info": BENTO_INFO})

        conf, configure = prepare_configure(top_node, BENTO_INFO, self._configure_context)
        configure.run(conf)
        conf.shutdown()
        pkg = conf.pkg

        bld, build = prepare_build(top_node, conf.pkg, context_klass=self._build_context)
        build.run(bld)
        build.shutdown(bld)

    def test_simple_extension(self):
        top_node = self.root.srcnode

        create_fake_package_from_bento_infos(top_node, {"bento.info": BENTO_INFO_WITH_EXT})

        conf, configure = prepare_configure(top_node, BENTO_INFO_WITH_EXT, self._configure_context)
        configure.run(conf)
        conf.shutdown()
        pkg = conf.pkg

        bld, build = prepare_build(top_node, conf.pkg, context_klass=self._build_context)
        build.run(bld)
        build.shutdown(bld)

        sections = build.section_writer.sections["extensions"]
        for extension in pkg.extensions.values():
            isection = sections[extension.name]
            self.assertTrue(os.path.exists(os.path.join(isection.source_dir, isection.files[0][0])))

    def test_extension_registration(self):
        top_node = self.root.srcnode

        bento_info = """\
Name: foo

Library:
    Extension: _foo
        Sources: src/foo.c
    Extension: _bar
        Sources: src/bar.c
"""

        create_fake_package_from_bento_infos(top_node, {"bento.info": bento_info})

        conf, configure = prepare_configure(top_node, bento_info, self._configure_context)
        configure.run(conf)
        conf.shutdown()

        bld, build = prepare_build(top_node, conf.pkg, context_klass=self._build_context)
        bld.pre_recurse(top_node)
        try:
            bld.register_builder("_bar", self._dummy)
        finally:
            bld.post_recurse()
        build.run(bld)
        build.shutdown(bld)

        sections = build.section_writer.sections["extensions"]
        self.failUnless(len(sections) == 2)
        self.failUnless(len(sections["_bar"].files) == 0)

class TestBuildDistutils(_TestBuildSimpleExtension):
    def setUp(self):
        from bento.commands.build_distutils import DistutilsBuilder
        _TestBuildSimpleExtension.setUp(self)
        self._distutils_builder = DistutilsBuilder()

        self._configure_context = DistutilsConfigureContext
        self._build_context = DistutilsBuildContext
        self._dummy = lambda extension: InstalledSection("extensions", extension.name, "", "", [])

class TestBuildYaku(_TestBuildSimpleExtension):
    def setUp(self):
        super(TestBuildYaku, self).setUp()

        ctx = get_cfg()
        ctx.use_tools(["ctasks", "pyext"])
        ctx.store()

        self.yaku_build = get_bld()

        self._configure_context = ConfigureYakuContext
        self._build_context = BuildYakuContext
        self._dummy = lambda extension: []

    def tearDown(self):
        try:
            self.yaku_build.store()
        finally:
            super(TestBuildYaku, self).tearDown()

class TestBuildCommand(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))

        self.old_dir = os.getcwd()
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

    def test_simple(self):
        root = self.root
        top_node = root.srcnode

        create_fake_package_from_bento_info(top_node, BENTO_INFO)
        conf, configure = prepare_configure(top_node, BENTO_INFO, ConfigureYakuContext)
        configure.run(conf)
        conf.shutdown()

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        bld = BuildYakuContext([], opts, conf.pkg, top_node)
        build.run(bld)
