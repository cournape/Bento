from distutils.command.build \
    import \
        build as old_build

class build(old_build):
    cmd_name = "build"
    def run(self):
        self.run_command("config")
        self.distribution.run_command_in_context(self.cmd_name, [])
