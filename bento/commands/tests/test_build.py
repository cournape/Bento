import os
import sys
import shutil
import tempfile

import os.path as op

from six.moves \
    import \
        cStringIO

from bento.compat.api.moves \
    import \
        unittest


from bento.core.options \
    import \
        PackageOptions
from bento.core.package \
    import \
        PackageDescription
from bento.core.testing\
    import \
        expected_failure, skip_if
from bento.core.node \
    import \
        create_base_nodes
from bento.core.utils \
    import \
        subst_vars
from bento.backends.distutils_backend \
    import \
        DistutilsBuildContext, DistutilsConfigureContext
from bento.backends.yaku_backend \
    import \
        BuildYakuContext, ConfigureYakuContext
from bento.commands.hooks \
    import \
        PreHookWrapper
from bento.commands.wrapper_utils \
    import \
        run_command_in_context
from bento.commands.options \
    import \
        OptionsContext
from bento.commands.build \
    import \
        BuildCommand
from bento.core.testing \
    import \
        create_fake_package_from_bento_infos, create_fake_package_from_bento_info, \
        require_c_compiler
from bento.commands.tests.utils \
    import \
        prepare_configure, prepare_build, EncodedStringIO, \
        prepare_command, create_global_context
from bento.errors \
    import \
        UsageException


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
    # Those should be set by subclasses
    _configure_context = None
    _build_context = None
    def setUp(self):
        self.save = None
        self.d = None

        self.save = os.getcwd()
        self.d = tempfile.mkdtemp()
        os.chdir(self.d)

        try:
            self.top_node, self.build_node, self.run_node = \
                    create_base_nodes(self.d, os.path.join(self.d, "build"))

            def builder_factory(build_context):
                def _dummy(extension):
                    from_node = self.build_node

                    pkg_dir = op.dirname(extension.name.replace('.', op.sep))
                    target_dir = op.join('$sitedir', pkg_dir)
                    build_context.outputs_registry.register_outputs("extensions",
                        extension.name, [], from_node, target_dir)
                return _dummy

            self._builder_factory = builder_factory
        except:
            os.chdir(self.save)
            raise

    def tearDown(self):
        if self.save:
            os.chdir(self.save)
        if self.d:
            shutil.rmtree(self.d)

    def _run_configure_and_build(self, bentos, bscripts=None, configure_argv=None, build_argv=None):
        conf, configure, bld, build = self._run_configure(bentos, bscripts,
                configure_argv, build_argv)
        run_command_in_context(bld, build)

        return conf, configure, bld, build

    def _run_configure(self, bentos, bscripts=None, configure_argv=None, build_argv=None):
        top_node = self.top_node

        create_fake_package_from_bento_infos(top_node, bentos, bscripts)

        conf, configure = prepare_configure(top_node, bentos["bento.info"], self._configure_context)
        run_command_in_context(conf, configure)

        bld, build = prepare_build(top_node, bentos["bento.info"], self._build_context, build_argv)

        return conf, configure, bld, build

    def _resolve_isection(self, node, isection):
        source_dir = subst_vars(isection.source_dir, {"_srcrootdir": self.build_node.abspath()})
        isection.source_dir = source_dir
        return isection

    def test_no_extension(self):
        self._run_configure_and_build({"bento.info": BENTO_INFO})

    def test_simple_extension(self):
        conf, configure, bld, build = self._run_configure_and_build({"bento.info": BENTO_INFO_WITH_EXT})

        sections = bld.section_writer.sections["extensions"]
        for extension in conf.pkg.extensions.values():
            isection = self._resolve_isection(bld.run_node, sections[extension.name])
            self.assertTrue(os.path.exists(os.path.join(isection.source_dir, isection.files[0][0])))

    def test_disable_extension(self):
        conf, configure, bld, build = self._run_configure({"bento.info": BENTO_INFO_WITH_EXT})
        pre_hook = PreHookWrapper(lambda context: context.disable_extension("foo"),
                                  "build", self.d)
        run_command_in_context(bld, build, pre_hooks=[pre_hook])

        assert "extensions" not in bld.section_writer.sections

    @expected_failure
    def test_disable_nonexisting_extension(self):
        conf, configure, bld, build = self._run_configure({"bento.info": BENTO_INFO_WITH_EXT})

        pre_hook = PreHookWrapper(lambda context: context.disable_extension("foo2"),
                                  "build", self.d)
        run_command_in_context(bld, build, pre_hooks=[pre_hook])

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

        conf, configure, bld, build = self._run_configure(bentos)

        def pre_build(context):
            builder = self._builder_factory(context)
            context.register_builder("_bar", builder)
        pre_hook = PreHookWrapper(pre_build, "build", self.d)
        run_command_in_context(bld, build, pre_hooks=[pre_hook])

        sections = bld.section_writer.sections["extensions"]
        self.failUnless(len(sections) == 2)
        self.failUnless(len(sections["_bar"].files) == 0)

    def test_extension_tweak(self):
        bento_info = """\
Name: foo

Library:
    Extension: _foo
        Sources: src/foo.c
    Extension: _bar
        Sources: src/bar.c
"""
        bentos = {"bento.info": bento_info}

        conf, configure, bld, build = self._run_configure(bentos)

        # To check that include_dirs is passed along the slightly
        # over-engineered callchain, we wrap the default build with a function
        # that check the include_dirs is step up correctly.
        def pre_build(context):
            context.tweak_builder("_bar", include_dirs=["fubar"])
        pre_hook = PreHookWrapper(pre_build, "build", self.d)
        old_default_builder = bld.default_builder
        try:
            def _builder_wrapper(extension, **kw):
                if extension.name == "_bar":
                    self.assertTrue(kw.get("include_dirs", []) == ["fubar"])
                return old_default_builder(extension, **kw)
            bld.default_builder = _builder_wrapper
            run_command_in_context(bld, build, pre_hooks=[pre_hook])
        finally:
            bld.default_builder = old_default_builder

        sections = bld.section_writer.sections["extensions"]
        self.failUnless(len(sections) == 2)

    def test_simple_library(self):
        conf, configure, bld, build = self._run_configure_and_build({"bento.info": BENTO_INFO_WITH_CLIB})
        sections = bld.section_writer.sections["compiled_libraries"]
        for library in conf.pkg.compiled_libraries.values():
            isection = self._resolve_isection(bld.run_node, sections[library.name])
            self.assertTrue(os.path.exists(os.path.join(isection.source_dir, isection.files[0][0])))

    def test_simple_inplace(self):
        _, _, bld, build = self._run_configure_and_build({"bento.info": BENTO_INFO_WITH_EXT}, build_argv=["-i"])
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
        super(TestBuildDistutils, self).test_simple_library()

    @require_c_compiler("distutils")
    def test_simple_extension(self):
        super(TestBuildDistutils, self).test_simple_extension()

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
        import bento.backends.waf_backend
        bento.backends.waf_backend.disable_output()
        return False
    except SyntaxError:
        return True
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

    def _run_configure(self, bentos, bscripts=None, configure_argv=None, build_argv=None):
        from bento.backends.waf_backend import make_stream_logger
        from bento.backends.waf_backend import WafBackend

        top_node = self.top_node

        bento_info = bentos["bento.info"]
        package = PackageDescription.from_string(bento_info)
        package_options = PackageOptions.from_string(bento_info)

        create_fake_package_from_bento_info(top_node, bento_info)
        top_node.make_node("bento.info").safe_write(bento_info)

        global_context = create_global_context(package, package_options, WafBackend())
        conf, configure = prepare_command(global_context, "configure",
                configure_argv, package, top_node)
        run_command_in_context(conf, configure)

        bld, build = prepare_command(global_context, "build", build_argv, package, top_node)
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

    @skip_no_waf
    def test_extension_tweak(self):
        super(TestBuildWaf, self).test_extension_tweak()

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
            from bento.backends.waf_backend import ConfigureWafContext, BuildWafContext

            self._configure_context = ConfigureWafContext
            self._build_context = BuildWafContext

    def tearDown(self):
        super(TestBuildWaf, self).tearDown()
        sys.stderr = self._stderr
        sys.stdout = self._stdout

class TestBuildCommand(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.top_node, self.build_node, self.run_node = create_base_nodes(self.d, os.path.join(self.d, "build"))

        self.old_dir = os.getcwd()
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

    def _execute_build(self, bento_info):
        create_fake_package_from_bento_info(self.top_node, bento_info)
        conf, configure = prepare_configure(self.top_node, bento_info, ConfigureYakuContext)
        run_command_in_context(conf, configure)

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        bld = BuildYakuContext(None, [], opts, conf.pkg, self.top_node)
        run_command_in_context(bld, build)

        return bld

    def test_simple(self):
        self._execute_build(BENTO_INFO)

    def test_executables(self):
        bento_info = """\
Name: foo

Library:
    Packages: foo

Executable: foomaker
    Module: foomain
    Function: main
"""
        self._execute_build(bento_info)

    def test_config_py(self):
        bento_info = """\
Name: foo

ConfigPy: foo/__config.py

Library:
    Packages: foo
"""
        self._execute_build(bento_info)

    def test_meta_template_file(self):
        bento_info = """\
Name: foo

MetaTemplateFile: foo/__package_info.py.in

Library:
    Packages: foo
"""
        n = self.top_node.make_node(op.join("foo", "__package_info.py.in"))
        n.parent.mkdir()
        n.write("""\
NAME = $NAME
""")
        self._execute_build(bento_info)
        package_info = self.build_node.find_node(op.join("foo", "__package_info.py"))

        r_package_info = """\
NAME = "foo"
"""
        self.assertEqual(package_info.read(), r_package_info)

class TestBuildDirectoryBase(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

        try:
            self.top_node, self.build_node, self.run_node = create_base_nodes(self.d,
                    os.path.join(self.d, "yoyobuild"))

            self.old_dir = os.getcwd()
            os.chdir(self.d)
        except:
            shutil.rmtree(self.d)
            raise

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

class TestBuildDirectory(TestBuildDirectoryBase):
    def test_simple_yaku(self):
        top_node = self.top_node

        create_fake_package_from_bento_info(top_node, BENTO_INFO_WITH_EXT)
        conf, configure = prepare_configure(top_node, BENTO_INFO_WITH_EXT, ConfigureYakuContext)
        run_command_in_context(conf, configure)

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        bld = BuildYakuContext(None, [], opts, conf.pkg, top_node)
        run_command_in_context(bld, build)

    def test_simple_distutils(self):
        top_node = self.top_node

        create_fake_package_from_bento_info(top_node, BENTO_INFO_WITH_EXT)
        conf, configure = prepare_configure(top_node, BENTO_INFO_WITH_EXT, DistutilsConfigureContext)
        run_command_in_context(conf, configure)

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        bld = DistutilsBuildContext(None, [], opts, conf.pkg, top_node)
        run_command_in_context(bld, build)

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
        from bento.backends.waf_backend import make_stream_logger
        from bento.backends.waf_backend import WafBackend

        top_node = self.top_node

        package = PackageDescription.from_string(BENTO_INFO_WITH_EXT)
        package_options = PackageOptions.from_string(BENTO_INFO_WITH_EXT)

        create_fake_package_from_bento_info(top_node, BENTO_INFO_WITH_EXT)
        top_node.make_node("bento.info").safe_write(BENTO_INFO_WITH_EXT)

        global_context = create_global_context(package, package_options, WafBackend())
        conf, configure = prepare_command(global_context, "configure", [], package, top_node)
        run_command_in_context(conf, configure)

        bld, build = prepare_command(global_context, "build", [], package, top_node)
        bld.waf_context.logger = make_stream_logger("build", cStringIO())
        run_command_in_context(bld, build)
