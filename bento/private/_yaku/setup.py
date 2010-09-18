from distutils.core \
    import \
        setup

setup(name="yaku",
    description="A simple build system in python to build python extensions",
    long_description=open("README").read(),
    version="0.0.1",
    author="David Cournapeau",
    author_email="cournape@gmail.com",
    license="BSD",
    packages=["yaku.tools", "yaku", "yaku.compat"],
)
