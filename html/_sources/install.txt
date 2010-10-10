Installing bento
==================

setuptools-based installation (deprecated)
------------------------------------------

Bento has a setup.py file, and can be installed as any other
conventional python software::

    python setup.py install --user # for python >= 2.6
    python setup.py install # otherwise

bento-based installer
-----------------------

Bento is now able to install itself. First, you need to create the bentomaker script::

    python bootstrap.py

This will create a script (or an exe on windows) which can be used to
install bento. Once created, bento is installed as a regular
bento package::

    ./bentomaker configure
    ./bentomaker build
    ./bentomaker install 
    # Or an egg
    ./bentomaker build_egg 
    # Or a windows installer
    ./bentomaker build_wininst
