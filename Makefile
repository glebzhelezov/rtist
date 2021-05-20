LIB_DIR = lib
VERSION := $(shell git describe --tags)

default: trippy

binary: trippy
	pyinstaller -F --hidden-import array --hidden-import cysignals bin/mediantriplet
	pyinstaller -F --hidden-import array bin/tripthrough
	rm mediantriplet.spec
	rm tripthrough.spec


trippy: setup.py src/trippy/*.pyx libctriplet.a tags
	rm -fv src/trippy/*.c
	# python setup.py build_ext --inplace
	# python setup.py develop
	python setup.py develop

libctriplet.a:
	make -C $(LIB_DIR) libctriplet.a

tags:
	echo "__version__ = \"$(VERSION)\"" > src/trippy/median_triplet_version.py

cleanall: clean libcleanall
	rm -rfv dist

clean: libcleanall
	python setup.py clean --all
	rm -fv src/trippy/*.c

libclean:
	make -C $(LIB_DIR) clean

libcleanall:
	make -C $(LIB_DIR) cleanall
