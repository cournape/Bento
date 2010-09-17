from yaku.tests.test_helpers \
    import \
        TmpContextBase
from yaku.context \
    import \
        get_cfg, get_bld

class ContextTest(TmpContextBase):
    def test_load_store_simple(self):
        """Test one can load and store the contexts."""
        ctx = get_cfg()
        ctx.store()

        ctx = get_bld()
        ctx.store()
