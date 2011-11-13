from distutils.command.build \
    import \
        build as old_build

class build(old_build):
    cmd_name = "build"
    def __init__(self, *a, **kw):
        old_build.__init__(self, *a, **kw)

    def initialize_options(self):
        old_build.initialize_options(self)

    def finalize_options(self):
        old_build.finalize_options(self)

    def run(self):
        self.run_command("config")
        self.distribution.run_command_in_context(self.cmd_name, [])
