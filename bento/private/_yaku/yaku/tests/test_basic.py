from yaku.tests.test_helpers \
    import \
        TmpContextBase
from yaku.context \
    import \
        get_cfg, get_bld
from yaku.conftests \
    import \
        check_compiler

class ContextTest(TmpContextBase):
    def test_load_store_simple(self):
        """Test one can load and store the contexts."""
        ctx = get_cfg()
        ctx.store()

        ctx = get_bld()
        ctx.store()

class SimpleCCTest(TmpContextBase):
    def test_compiler(self):
        ctx = get_cfg()
        ctx.store()

        ctx = get_bld()
        ctx.store()

