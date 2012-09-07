import os.path as op

import bento.utils.path

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

class DataFiles(object):
    @classmethod
    def from_parse_dict(cls, d):
        return cls(**d)

    def __init__(self, name, files=None, target_dir=None, source_dir=None):
        self.name = name

        if files is not None:
            self.files = files
        else:
            self.files = []

        if target_dir is not None:
            self.target_dir = target_dir
        else:
            self.target_dir = "$sitedir"

        if source_dir is not None:
            self.source_dir = source_dir
        else:
            self.source_dir = "."

    def __repr__(self):
        return "DataSection(files=%r, target_dir=%r, source_dir=%r)" % \
               (self.files, self.target_dir, self.source_dir)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

class Executable(object):
    @classmethod
    def from_parse_dict(cls, d):
        return cls(**d)

    @classmethod
    def from_representation(cls, s):
        if not "=" in s:
            raise ValueError("s should be of the form name=module:function")
        name, value = [j.strip() for j in s.split("=")]
        if not ":" in value:
            raise ValueError(
                "string representation should be of the form module:function, not %s"
                % value)
        module, function = value.split(":", 1)
        return cls(name, module, function)

    def __init__(self, name, module, function):
        # FIXME: check that module is a module name ?
        self.name = name
        self.module = module
        self.function = function

    # FIXME: this function should not really be here...
    def representation(self):
        return ":".join([self.module, self.function])

    # FIXME: this function should not really be here...
    def full_representation(self):
        return "%s = %s" % (self.name, self.representation())

    def __repr__(self):
        return repr({"name": self.name, "module": self.module, "function": self.function})

class Compiled(object):
    @classmethod
    def from_parse_dict(cls, d):
        return cls(**d)

    def __init__(self, name, sources, include_dirs=None):
        self.name = name
        self.base_name = op.basename(name)
        self.sources = [bento.utils.path.normalize_path(p) for p in sources]
        if include_dirs is None:
            self.include_dirs = []
        else:
            self.include_dirs = include_dirs

    def __str__(self):
        return "%s(%s, %s, %s)" % (self.__class__.__name__, self.name,
                                   self.sources, self.include_dirs)

    def __eq__(self, other):
        return self.name == other.name \
                and self.sources == other.sources \
                and self.include_dirs == other.include_dirs

    #def __repr__(self):
    #    return self.__str__()

class Extension(Compiled):
    pass

class CompiledLibrary(Compiled):
    pass
