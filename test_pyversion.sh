#! /bin/sh
rm -rf build && python2.4 bootstrap.py && ./bentomaker test
rm -rf build && python2.6 -m nose.core --processes=4 bento
rm -rf build && python2.7 -m nose.core --processes=4 bento
rm -rf build && python3.2 -m nose.core --processes=4 bento
