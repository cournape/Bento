class InstalledPkgDescription(object):
    def __init__(self, files, path_options):
        self.files = files
        self._path_variables = path_options

        self._path_variables['_srcrootdir'] = "."

    def write(self, filename):
        fid = open(filename, "w")
        try:
            path_fields = "\n".join([
                "\t%s=%s" % (name, value) for name, value in
                                              self._path_variables.items()])

            path_section = """\
paths
%s
!- FILELIST
""" % path_fields
            fid.write(path_section)

            for name, value in self.files.items():
                if name in ["pythonfiles"]:
                    source = "$_srcrootdir"
                section = """\
%(section)s
%(source)s
%(target)s
%(files)s
""" % {"section": name,
       "source": "\tsource=%s" % source,
       "target": "\ttarget=%s" % value["target"],
       "files": "\n".join(["\t%s" % f for f in value["files"]])}
                fid.write(section)

        finally:
            fid.close()

if __name__ == "__main__":
    files = {}
    files["pythonfiles"] = {
            "files": ["hello.py"],
            "target": "$sitedir",
            }
    p = InstalledPkgDescription(files,
                                {"sitedir": "/usr/lib/python26/site-packages"})
    p.write("yo.txt")
