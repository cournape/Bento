#! /bin/sh
tests="examples/chaining/build.py
examples/conf_example.py
examples/example4.py
examples/example5.py
examples/example.py
examples/file_hook.py
examples/fortran/conf_fortran.py
examples/fortran/fortran.py
examples/node_example.py
examples/override_ext.py
examples/pyext_example.py
examples/test_env.py"
for i in $tests; do
	echo "======== TESTING $i ============="
	rm -rf examples/build;
	f=`basename $i`;
	d=`dirname $i`;
	(cd $d && python $f);
done
