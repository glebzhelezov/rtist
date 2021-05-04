LIB_DIR = lib
VERSION := $(shell git describe --tags)

default: binary

binary: comb2
	pyinstaller -F --hidden-import array --hidden-import cysignals median_triplet.py

comb2: setup.py triplet_omp_py.pyx libctriplet.a tags
	python setup.py build_ext --inplace
#	python setup.py develop

libctriplet.a:
	make -C $(LIB_DIR) libctriplet.a

tags:
	echo "__version__ = \"$(VERSION)\"" > median_triplet_version.py

cleanall: clean libcleanall
	rm -rfv dist
	rm -fv *.so

clean: libcleanall
	rm -fv comb2.c
	rm -rfv build
	rm -fv bitsnbobs.c
	rm -fv scipy_comb.c
	rm -fv triplet_omp_py.c
	rm -rfv build
	rm -fv median_triplet.spec

libclean:
	make -C $(LIB_DIR) clean

libcleanall:
	make -C $(LIB_DIR) cleanall
