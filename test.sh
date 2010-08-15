#! /bin/sh
for i in examples/*.py; do
	echo "======== TESTING $i ============="
	rm -rf examples/build;
	f=`basename $i`;
	(cd examples && python $f);
done
