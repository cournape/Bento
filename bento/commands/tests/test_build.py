import os
import sys
import shutil
import tempfile
import types

import os.path as op

from six.moves \
    import \
        cStringIO

from bento.compat.api.moves \
    import \
        unittest

from bento.core.testing\
    import \
        expected_failure, skip_if
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.core.utils \
    import \
        subst_vars
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
from bento.commands.api \
    import \
        UsageException

import bento.commands.build_distutils
import bento.commands.build_yaku

from yaku.context \
    import \
        get_bld, get_cfg

from bento.core.testing \
    import \
        create_fake_package_from_bento_infos, create_fake_package_from_bento_info, \
        require_c_compiler
from bento.commands.tests.utils \
    import \
        prepare_configure, prepare_build, prepare_options, EncodedStringIO

BENTO_INFO_WITH_EXT = """\
Name: foo

Library:
    Extension: foo
        Sources: foo.c
"""

BENTO_INFO_WITH_CLIB = """\
Name: foo

Library:
    CompiledLibrary: foo
        Sources: foo.c
"""

BENTO_INFO = """\
Name: foo

Library:
    Packages: foo, foo.bar
    Modules: fubar
"""

class _TestBuildSimpleExtension(unittest.TestCase):
    def setUp(self):
        self.save = None
        self.d = None

        self.save = os.getcwd()
        self.d = tempfile.mkdtemp()
        os.chdir(self.d)

        root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))
        self.top_node = root._ctx.srcnode
        self.build_node = root._ctx.bldnode

        # Those should be set by subclasses
        self._configure_context = None
        self._build_context = None

        def builder_factory(build_context):
            def _dummy(extension):
                from_node = self.build_node

                pkg_dir = op.dirname(extension.name.replace('.', op.sep))
                target_dir = op.join('$sitedir', pkg_dir)
                build_context.outputs_registry.register_outputs("extensions",
                    extension.name, [], from_node, target_dir)
            return _dummy

        self._builder_factory = builder_factory

        #self._dummy_builder = None

    def tearDown(self):
        if self.save:
            os.chdir(self.save)
        if self.d:
            shutil.rmtree(self.d)

    def _prepare(self, bentos, bscripts=None, configure_args=None, build_args=None):
        conf, configure, bld, build = self._create_contexts(bentos, bscripts,
                configure_args, build_args)

        build.run(bld)
        build.shutdown(bld)
        return conf, configure, bld, build

    def _create_contexts(self, bentos, bscripts=None, configure_args=None, build_args=None):
        top_node = self.top_node

        create_fake_package_from_bento_infos(top_node, bentos, bscripts)

        conf, configure = prepare_configure(top_node, bentos["bento.info"], self._configure_context)
        configure.run(conf)
        conf.shutdown()

        bld, build = prepare_build(top_node, conf.pkg,
                conf.package_options, self._build_context, build_args)
        return conf, configure, bld, build

    def _resolve_isection(self, node, isection):
        source_dir = subst_vars(isection.source_dir, {"_srcrootdir": self.build_node.abspath()})
        isection.source_dir = source_dir
        return isection

    def test_no_extension(self):
        self._prepare({"bento.info": BENTO_INFO})

    def test_simple_extension(self):
        conf, configure, bld, build = self._prepare({"bento.info": BENTO_INFO_WITH_EXT})

        sections = bld.section_writer.sections["extensions"]
        for extension in conf.pkg.extensions.values():
            isection = self._resolve_isection(bld.run_node, sections[extension.name])
            self.assertTrue(os.path.exists(os.path.join(isection.source_dir, isection.files[0][0])))

    def test_disable_extension(self):
        conf, configure, bld, build = self._create_contexts({"bento.info": BENTO_INFO_WITH_EXT})

        bld.pre_recurse(self.top_node)
        try:
            bld.disable_extension("foo")
        finally:
            bld.post_recurse()
        build.run(bld)
        build.shutdown(bld)

        assert "extensions" not in bld.section_writer.sections

    @expected_failure
    def test_disable_nonexisting_extension(self):
        conf, configure, bld, build = self._create_contexts({"bento.info": BENTO_INFO_WITH_EXT})

        bld.pre_recurse(self.top_node)
        try:
            bld.disable_extension("foo2")
        finally:
            bld.post_recurse()
        build.run(bld)
        build.shutdown(bld)

        assert "extensions" not in bld.section_writer.sections

    def test_extension_registration(self):
        top_node = self.top_node

        bento_info = """\
Name: foo

Library:
    Extension: _foo
        Sources: src/foo.c
    Extension: _bar
        Sources: src/bar.c
"""
        bentos = {"bento.info": bento_info}

        conf, configure, bld, build = self._create_contexts(bentos)
        configure.run(conf)
        conf.shutdown()

        #bld, build = prepare_build(top_node, conf.pkg, context_klass=self._build_context)
        bld.pre_recurse(top_node)
        try:
            builder = self._builder_factory(bld)
            bld.register_builder("_bar", builder)
        finally:
            bld.post_recurse()
        build.run(bld)
        build.shutdown(bld)

        sections = bld.section_writer.sections["extensions"]
        self.failUnless(len(sections) == 2)
        self.failUnless(len(sections["_bar"].files) == 0)

    def test_simple_library(self):
        conf, configure, bld, build = self._prepare({"bento.info": BENTO_INFO_WITH_CLIB})
        sections = bld.section_writer.sections["compiled_libraries"]
        for library in conf.pkg.compiled_libraries.values():
            isection = self._resolve_isection(bld.run_node, sections[library.name])
            self.assertTrue(os.path.exists(os.path.join(isection.source_dir, isection.files[0][0])))

    def test_simple_inplace(self):
        conf, configure, bld, build = self._prepare({"bento.info": BENTO_INFO_WITH_EXT}, build_args=["-i"])
        sections = bld.section_writer.sections["extensions"]
        source_dir = bld.top_node.abspath()
        for section in sections.values():
            isection = self._resolve_isection(bld.run_node, section)
            for f in isection.files[0]:
                self.assertTrue(op.exists(op.join(source_dir, f)))

class TestBuildDistutils(_TestBuildSimpleExtension):
    def setUp(self):
        from bento.commands.build_distutils import DistutilsBuilder
        _TestBuildSimpleExtension.setUp(self)
        self._distutils_builder = DistutilsBuilder()

        self._configure_context = DistutilsConfigureContext
        self._build_context = DistutilsBuildContext

    @require_c_compiler("distutils")
    def test_simple_inplace(self):
        super(TestBuildDistutils, self).test_simple_inplace()

    @require_c_compiler("distutils")
    def test_extension_registration(self):
        super(TestBuildDistutils, self).test_extension_registration()

    @require_c_compiler("distutils")
    def test_simple_library(self):
        super(TestBuildDistutils, self).test_extension_registration()

    @require_c_compiler("distutils")
    def test_simple_extension(self):
        super(TestBuildDistutils, self).test_extension_registration()

class TestBuildYaku(_TestBuildSimpleExtension):
    def setUp(self):
        super(TestBuildYaku, self).setUp()

        self._configure_context = ConfigureYakuContext
        self._build_context = BuildYakuContext

    @require_c_compiler("yaku")
    def test_simple_inplace(self):
        super(TestBuildYaku, self).test_simple_inplace()

    @require_c_compiler("yaku")
    def test_extension_registration(self):
        super(TestBuildYaku, self).test_extension_registration()

    @require_c_compiler("yaku")
    def test_simple_library(self):
        super(TestBuildYaku, self).test_simple_library()

    @require_c_compiler("yaku")
    def test_simple_extension(self):
        super(TestBuildYaku, self).test_simple_extension()

    @require_c_compiler("yaku")
    def test_disable_extension(self):
        super(TestBuildYaku, self).test_disable_extension()

    @require_c_compiler("yaku")
    def test_disable_nonexisting_extension(self):
        super(TestBuildYaku, self).test_disable_nonexisting_extension()

def _not_has_waf():
    try:
        import bento.commands.extras.waf
        bento.commands.extras.waf.disable_output()
        return False
    except UsageException:
        return True

def skip_no_waf(f):
    return skip_if(_not_has_waf(), "waf not found")(f)

class TestBuildWaf(_TestBuildSimpleExtension):
    #def __init__(self, *a, **kw):
    #    super(TestBuildWaf, self).__init__(*a, **kw)

    #    # Add skip_no_waf decorator to any test function
    #    for m in dir(self):
    #        a = getattr(self, m)
    #        if isinstance(a, types.MethodType) and _NOSE_CONFIG.testMatch.match(m):
    #            setattr(self, m, skip_no_waf(a))

    def _create_contexts(self, bentos, bscripts=None, configure_args=None, build_args=None):
        conf, configure, bld, build = super(TestBuildWaf, self)._create_contexts(
                bentos, bscripts, configure_args, build_args)
        from bento.commands.extras.waf import make_stream_logger
        bld.waf_context.logger = make_stream_logger("build", cStringIO())

        return conf, configure, bld, build

    @skip_no_waf
    def test_simple_extension(self):
        super(TestBuildWaf, self).test_simple_extension()

    @skip_no_waf
    def test_simple_library(self):
        super(TestBuildWaf, self).test_simple_library()

    @skip_no_waf
    def test_no_extension(self):
        super(TestBuildWaf, self).test_no_extension()

    @skip_no_waf
    def test_extension_registration(self):
        super(TestBuildWaf, self).test_extension_registration()

    @skip_no_waf
    def test_disable_extension(self):
        super(TestBuildWaf, self).test_disable_extension()

    @skip_no_waf
    def test_disable_nonexisting_extension(self):
        super(TestBuildWaf, self).test_disable_extension()

    @skip_no_waf
    def test_simple_inplace(self):
        super(TestBuildWaf, self).test_simple_inplace()

    def setUp(self):
        self._fake_output = None
        self._stderr = sys.stderr
        self._stdout = sys.stdout
        super(TestBuildWaf, self).setUp()
        # XXX: ugly stuff to make waf and nose happy together
        sys.stdout = EncodedStringIO()
        sys.stderr = EncodedStringIO()

        if _not_has_waf():
            return
        else:
            from bento.commands.extras.waf import ConfigureWafContext, BuildWafContext

            self._configure_context = ConfigureWafContext
            self._build_context = BuildWafContext

    def tearDown(self):
        super(TestBuildWaf, self).tearDown()
        sys.stderr = self._stderr
        sys.stdout = self._stdout

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
        top_node = root.find_node(self.d)

        create_fake_package_from_bento_info(top_node, BENTO_INFO)
        conf, configure = prepare_configure(top_node, BENTO_INFO, ConfigureYakuContext)
        configure.run(conf)
        conf.shutdown()

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        bld = BuildYakuContext(None, [], opts, conf.pkg, top_node)
        build.run(bld)

class TestBuildDirectoryBase(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

        self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "yoyobuild"))
        self.top_node = self.root.find_node(self.d)
        self.run_node = self.top_node

        self.old_dir = os.getcwd()
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

class TestBuildDirectory(TestBuildDirectoryBase):
    def test_simple_yaku(self):
        top_node = self.top_node

        create_fake_package_from_bento_info(top_node, BENTO_INFO_WITH_EXT)
        conf, configure = prepare_configure(top_node, BENTO_INFO_WITH_EXT, ConfigureYakuContext)
        configure.run(conf)
        conf.shutdown()

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        bld = BuildYakuContext(None, [], opts, conf.pkg, top_node)
        build.run(bld)

    def test_simple_distutils(self):
        top_node = self.top_node

        create_fake_package_from_bento_info(top_node, BENTO_INFO_WITH_EXT)
        conf, configure = prepare_configure(top_node, BENTO_INFO_WITH_EXT, DistutilsConfigureContext)
        configure.run(conf)
        conf.shutdown()

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        bld = DistutilsBuildContext(None, [], opts, conf.pkg, top_node)
        build.run(bld)

class TestBuildDirectoryWaf(TestBuildDirectoryBase):
    def setUp(self):
        TestBuildDirectoryBase.setUp(self)

        self._stderr = sys.stderr
        self._stdout = sys.stdout

        sys.stdout = EncodedStringIO()
        sys.stderr = EncodedStringIO()

    def tearDown(self):
        sys.stderr = self._stderr
        sys.stdout = self._stdout

        TestBuildDirectoryBase.tearDown(self)

    @skip_no_waf
    def test_simple_waf(self):
        from bento.commands.extras.waf import ConfigureWafContext, BuildWafContext, \
                                              make_stream_logger, register_options

        top_node = self.top_node

        create_fake_package_from_bento_info(top_node, BENTO_INFO_WITH_EXT)
        conf, configure = prepare_configure(top_node, BENTO_INFO_WITH_EXT, ConfigureWafContext)
        configure.run(conf)
        conf.shutdown()

        build = BuildCommand()
        #opts = OptionsContext.from_command(build)
        opts = prepare_options("build", build, BuildWafContext)

        bld = BuildWafContext(None, [], opts, conf.pkg, top_node)
        bld.waf_context.logger = make_stream_logger("build", cStringIO())
        build.run(bld)
