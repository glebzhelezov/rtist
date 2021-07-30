LIB_DIR = lib
VERSION := $(shell git describe --tags)

default: mtrip

binary: mtrip
	pyinstaller -F --hidden-import array --hidden-import cysignals scripts/mediantriplet
	pyinstaller -F --hidden-import array scripts/tripthrough
	rm mediantriplet.spec
	rm tripthrough.spec


mtrip: setup.py src/mtrip/*.pyx libctriplet.a tags
	rm -fv src/mtrip/*.c
	# python setup.py build_ext --inplace
	# python setup.py develop
	python setup.py develop

libctriplet.a:
	make -C $(LIB_DIR) libctriplet.a

tags:
	echo "__version__ = \"$(VERSION)\"" > src/mtrip/median_triplet_version.py

cleanall: clean libcleanall
	rm -rfv dist

clean: libcleanall
	python setup.py clean --all
	rm -fv src/mtrip/*.c

libclean:
	make -C $(LIB_DIR) clean

libcleanall:
	make -C $(LIB_DIR) cleanall

uninstall:
	pip uninstall -y mtrip
