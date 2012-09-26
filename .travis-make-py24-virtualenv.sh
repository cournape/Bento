#!/bin/sh

VIRTENV=$1

set -x
set -e

curl -O http://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.7.2.tar.gz
curl -O http://www.python.org/ftp/python/2.4.6/Python-2.4.6.tar.bz2
tar xjf Python-2.4.6.tar.bz2
cd Python-2.4.6
cat >setup.cfg <<EOF
[build_ext]
library_dirs=/usr/lib/$(dpkg-architecture -qDEB_HOST_MULTIARCH)/
EOF
./configure --prefix=$PWD/install
make
make install
tar xzf virtualenv-1.7.2.tar.gz
(cd virtualenv-1.7.2 && ../install/bin/python2.4 setup.py install)
#virtualenv -p install/bin/python2.4 --distribute $VIRTENV
./install/bin/virtualenv -p install/bin/python2.4 --distribute $VIRTENV
