import os
import sys
import shutil
import unittest
import tempfile
import types

from cStringIO \
    import \
        StringIO

import nose
import nose.config

from nose.plugins.skip \
    import \
        SkipTest

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

_NOSE_CONFIG = nose.config.Config()

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

    def _prepare(self, bentos, bscripts=None):
        conf, configure, bld, build = self._create_contexts(bentos, bscripts)
        configure.run(conf)
        conf.shutdown()

        build.run(bld)
        build.shutdown(bld)
        return conf, configure, bld, build

    def _create_contexts(self, bentos, bscripts=None):
        top_node = self.root.srcnode

        create_fake_package_from_bento_infos(top_node, bentos, bscripts)

        conf, configure = prepare_configure(top_node, bentos["bento.info"], self._configure_context)

        bld, build = prepare_build(top_node, conf.pkg, context_klass=self._build_context)
        return conf, configure, bld, build

    def _resolve_isection(self, node, isection):
        source_dir = subst_vars(isection.source_dir, {"_srcrootdir": node.bldnode.abspath()})
        isection.source_dir = source_dir
        return isection

    def test_no_extension(self):
        self._prepare({"bento.info": BENTO_INFO})

    def test_simple_extension(self):
        conf, configure, bld, build = self._prepare({"bento.info": BENTO_INFO_WITH_EXT})

        sections = build.section_writer.sections["extensions"]
        for extension in conf.pkg.extensions.values():
            isection = self._resolve_isection(bld.top_node, sections[extension.name])
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
        bentos = {"bento.info": bento_info}

        conf, configure, bld, build = self._create_contexts(bentos)
        configure.run(conf)
        conf.shutdown()

        #bld, build = prepare_build(top_node, conf.pkg, context_klass=self._build_context)
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

    def test_simple_library(self):
        conf, configure, bld, build = self._prepare({"bento.info": BENTO_INFO_WITH_CLIB})
        sections = build.section_writer.sections["compiled_libraries"]
        for library in conf.pkg.compiled_libraries.values():
            isection = self._resolve_isection(bld.top_node, sections[library.name])
            self.assertTrue(os.path.exists(os.path.join(isection.source_dir, isection.files[0][0])))

class TestBuildDistutils(_TestBuildSimpleExtension):
    def setUp(self):
        from bento.commands.build_distutils import DistutilsBuilder
        _TestBuildSimpleExtension.setUp(self)
        self._distutils_builder = DistutilsBuilder()

        self._configure_context = DistutilsConfigureContext
        self._build_context = DistutilsBuildContext
        self._dummy = lambda extension: []

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

def _not_has_waf():
    try:
        import bento.commands.extras.waf
        bento.commands.extras.waf.disable_output()
        return False
    except RuntimeError, e:
        return True

def skip_no_waf(f):
    return skipif(_not_has_waf, "waf not found")(f)

def protect_streams_waf(func):
    """Run the given function in an environment where standard streams are
    directed to strings without making waf angry."""
    # This is not thread safe...
    set_stdout = False
    set_stderr = False
    try:
        if not hasattr(sys.stdout, "encoding"):
            sys.stdout.encoding = "ascii"
        if not hasattr(sys.stderr, "encoding"):
            sys.stderr.encoding = "ascii"
        func()
    finally:
        if set_stdout:
            del sys.stdout.encoding
        if set_stderr:
            del sys.stderr.encoding

class TestBuildWaf(_TestBuildSimpleExtension):
    #def __init__(self, *a, **kw):
    #    super(TestBuildWaf, self).__init__(*a, **kw)

    #    # Add skip_no_waf decorator to any test function
    #    for m in dir(self):
    #        a = getattr(self, m)
    #        if isinstance(a, types.MethodType) and _NOSE_CONFIG.testMatch.match(m):
    #            setattr(self, m, skip_no_waf(a))

    def _create_contexts(self, bentos, bscripts=None):
        conf, configure, bld, build = super(TestBuildWaf, self)._create_contexts(bentos, bscripts)
        from bento.commands.extras.waf import make_stream_logger
        from cStringIO import StringIO
        bld.waf_context.logger = make_stream_logger("build", StringIO())
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

    def setUp(self):
        self._fake_output = None
        self._stderr = sys.stderr
        self._stdout = sys.stdout
        super(TestBuildWaf, self).setUp()
        # XXX: ugly stuff to make waf and nose happy together
        if not hasattr(sys.stdout, "encoding"):
            sys.stdout.encoding = "ascii"
        if not hasattr(sys.stderr, "encoding"):
            sys.stderr.encoding = "ascii"

        if _not_has_waf():
            return
        else:
            from bento.commands.extras.waf import ConfigureWafContext, BuildWafContext

            self._configure_context = ConfigureWafContext
            self._build_context = BuildWafContext
            self._dummy = lambda extension: []

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
        top_node = root.srcnode

        create_fake_package_from_bento_info(top_node, BENTO_INFO)
        conf, configure = prepare_configure(top_node, BENTO_INFO, ConfigureYakuContext)
        configure.run(conf)
        conf.shutdown()

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        bld = BuildYakuContext([], opts, conf.pkg, top_node)
        build.run(bld)

class TestBuildDirectory(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

        self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "yoyobuild"))
        self.old_dir = os.getcwd()
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

    def test_simple_yaku(self):
        top_node = self.root.srcnode

        create_fake_package_from_bento_info(top_node, BENTO_INFO_WITH_EXT)
        conf, configure = prepare_configure(top_node, BENTO_INFO_WITH_EXT, ConfigureYakuContext)
        configure.run(conf)
        conf.shutdown()

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        bld = BuildYakuContext([], opts, conf.pkg, top_node)
        build.run(bld)

    def test_simple_distutils(self):
        top_node = self.root.srcnode

        create_fake_package_from_bento_info(top_node, BENTO_INFO_WITH_EXT)
        conf, configure = prepare_configure(top_node, BENTO_INFO_WITH_EXT, DistutilsConfigureContext)
        configure.run(conf)
        conf.shutdown()

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        bld = DistutilsBuildContext([], opts, conf.pkg, top_node)
        build.run(bld)

    @skip_no_waf
    def test_simple_waf(self):
        from bento.commands.extras.waf import ConfigureWafContext, BuildWafContext, make_stream_logger

        top_node = self.root.srcnode

        create_fake_package_from_bento_info(top_node, BENTO_INFO_WITH_EXT)
        conf, configure = prepare_configure(top_node, BENTO_INFO_WITH_EXT, ConfigureWafContext)
        configure.run(conf)
        conf.shutdown()

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        def _run():
            bld = BuildWafContext([], opts, conf.pkg, top_node)
            bld.waf_context.logger = make_stream_logger("build", StringIO())
            build.run(bld)
        protect_streams_waf(_run)
