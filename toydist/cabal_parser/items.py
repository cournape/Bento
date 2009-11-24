class FlagOption(object):
    def __init__(self, name, default_value, description=None):
        self.name = name
        self.default_value = default_value
        self.description = description

    def __str__(self):
        r = """\
Flag %s
    default value: %s
    description: %s"""
        return r % (self.name, self.default_value, self.description)

class PathOption(object):
    def __init__(self, name, default_value, description=None):
        self.name = name
        self.default_value = default_value
        self.description = description

    def __str__(self):
        r = """\
Customizable path: %s
    default value: %s
    description: %s"""
        return r % (self.name, self.default_value, self.description)
