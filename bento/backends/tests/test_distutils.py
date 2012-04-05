import os
import tempfile

from bento.commands.build_distutils \
    import \
        DistutilsBuilder
from bento.compat.api.moves \
    import \
        unittest
from bento.core.node \
    import \
        create_base_nodes
from bento.core.testing \
    import \
        require_c_compiler, DUMMY_C, DUMMY_CLIB
from bento.core.pkg_objects \
    import \
        Extension, CompiledLibrary

class TestDistutilsBuilder(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        new_cwd = tempfile.mkdtemp()
        os.chdir(new_cwd)
        try:
            self.top_node, self.build_node, self.run_node = create_base_nodes()
        except:
            os.chdir(self.old_cwd)
            raise

    def tearDown(self):
        os.chdir(self.old_cwd)

    #@require_c_compiler("distutils")
    def test_extension_simple(self):
        self.top_node.make_node("foo.c").write(DUMMY_C % {"name": "foo"})

        builder = DistutilsBuilder()
        extension = Extension("foo", ["foo.c"])
        builder.build_extension(extension)

    @require_c_compiler("distutils")
    def test_multiple_extensions(self):
        self.top_node.make_node("foo.c").write(DUMMY_C % {"name": "foo"})
        self.top_node.make_node("bar.c").write(DUMMY_C % {"name": "bar"})

        builder = DistutilsBuilder()

        extensions = [Extension("bar", ["bar.c"]), Extension("foo", ["foo.c"])]
        for extension in extensions:
            builder.build_extension(extension)

    @require_c_compiler("distutils")
    def test_clib_simple(self):
        self.top_node.make_node("foo.c").write(DUMMY_CLIB % {"name": "foo"})

        builder = DistutilsBuilder()
        extension = CompiledLibrary("foo", ["foo.c"])
        builder.build_compiled_library(extension)

    @require_c_compiler("distutils")
    def test_multiple_clibs(self):
        self.top_node.make_node("foo.c").write(DUMMY_CLIB % {"name": "foo"})
        self.top_node.make_node("bar.c").write(DUMMY_CLIB % {"name": "bar"})

        builder = DistutilsBuilder()

        extensions = [CompiledLibrary("bar", ["bar.c"]), CompiledLibrary("foo", ["foo.c"])]
        for extension in extensions:
            builder.build_compiled_library(extension)
