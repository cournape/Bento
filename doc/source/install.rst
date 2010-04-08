Installing toydist
==================

setuptools-based installation (deprecated)
------------------------------------------

Toydist has a setup.py file, and can be installed as any other
conventional python software::

    python setup.py install --user # for python >= 2.6
    python setup.py install # otherwise

toydist-based installer
-----------------------

Toydist is now able to install itself. First, you need to create the toymaker script::

    python bootstrap.py

This will create a script (or an exe on windows) which can be used to
install toydist. Once created, toydist is installed as a regular
toydist package::

    ./toymaker configure
    ./toymaker build
    ./toymaker install 
    # Or an egg
    ./toymaker build_egg 
    # Or a windows installer
    ./toymaker build_wininst
