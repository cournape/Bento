#! /bin/sh

MASTER_REPO=$PWD/../toydist.git
GH_PAGES_REPO=$PWD
MASTER_BRANCH=master
TEMPDIR=`mktemp -d /tmp/toydist.XXXXXX` || exit 1

if [ $MASTER_REPO/.git -ef $GH_PAGES_REPO/.git ]; then
	echo "You cannot run this script in the master repo (=$MASTER_REPO)"
	exit 1;
fi
echo $TEMPDIR

git checkout $MASTER_BRANCH || exit
git pull $MASTER_REPO $MASTER_BRANCH || exit

virtualenv bootstrap
. bootstrap/bin/activate
python setup.py install

(cd doc && make html)
mv doc/build/html $TEMPDIR
mv $TEMPDIR/html/_static $TEMPDIR/html/static
find $TEMPDIR/html -type f -exec sed -i '' -e s/_static/static/g '{}' \;
git checkout gh-pages || exit
rm -rf $GH_PAGES_REPO/*
mv $TEMPDIR/html/* $GH_PAGES_REPO
rm -rf $TEMPDIR
