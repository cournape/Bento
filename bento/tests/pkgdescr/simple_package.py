from bento.core import \
        PackageDescription
from bento.core.pkg_objects import \
        Extension

DESCR = """\
Name: Sphinx
Version: 0.6.3
Summary: Python documentation generator
Url: http://sphinx.pocoo.org/
DownloadUrl: http://pypi.python.org/pypi/Sphinx
Description: Some long description.
Author: Georg Brandl
AuthorEmail: georg@python.org
Maintainer: Georg Brandl
MaintainerEmail: georg@python.org
License: BSD
Platforms: any
Classifiers:
    Development Status :: 4 - Beta,
    Environment :: Console,
    Environment :: Web Environment,
    Intended Audience :: Developers,
    License :: OSI Approved :: BSD License,
    Operating System :: OS Independent,
    Programming Language :: Python,
    Topic :: Documentation,
    Topic :: Utilities

Library:
    Packages:
        sphinx,
        sphinx.builders
    Modules:
        cat.py
    Extension: _dog
        sources: src/dog.c
"""

PKG = PackageDescription(
    name="Sphinx",
    version="0.6.3",
    summary="Python documentation generator",
    url="http://sphinx.pocoo.org/",
    download_url="http://pypi.python.org/pypi/Sphinx",
    description="Some long description.",
    author="Georg Brandl",
    author_email="georg@python.org",
    maintainer="Georg Brandl",
    maintainer_email="georg@python.org",
    license="BSD",
    platforms=["any"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Documentation",
        "Topic :: Utilities",],
    py_modules=["cat.py"],
    packages=["sphinx", "sphinx.builders"],
    extensions={"_dog": Extension(name="_dog", sources=["src/dog.c"])},
)
