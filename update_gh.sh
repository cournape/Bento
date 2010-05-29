#! /bin/sh
OSNAME=`uname`
if test x"$OSNAME" = x"Linux"
then
	ISED="sed -i";
else
	ISED="sed -i ''";
fi

MASTER_REPO=$PWD/../bento-git
GH_PAGES_REPO=$PWD
MASTER_BRANCH=master
TEMPDIR=`mktemp -d /tmp/bento.XXXXXX` || exit 1

if [ $MASTER_REPO/.git -ef $GH_PAGES_REPO/.git ]; then
	echo "You cannot run this script in the master repo (=$MASTER_REPO)"
	exit 1;
fi
echo $TEMPDIR

# Force update to last master repo commit
git checkout $MASTER_BRANCH || exit
git fetch $MASTER_REPO $MASTER_BRANCH || exit
git reset --hard FETCH_HEAD || exit

virtualenv bootstrap
. bootstrap/bin/activate
# Installing sphinx into the virtualenv is necessary so that sphinx-build use
# the virtualenved python
easy_install sphinx
python setup.py install

(cd doc && make html)
mv doc/build/html $TEMPDIR
mv $TEMPDIR/html/_static $TEMPDIR/html/static
find $TEMPDIR/html -type f -exec $ISED -e s/_static/static/g '{}' \;
git checkout gh-pages || exit
rm -rf $GH_PAGES_REPO/*
mv $TEMPDIR/html/* $GH_PAGES_REPO
rm -rf $TEMPDIR
