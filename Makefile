LIB_DIR = lib

default: comb2

comb2: setup.py triplet_omp_py.pyx $(LIB_DIR)/libctriplet.a
	python setup.py build_ext --inplace && rm -f comb2.c && rm -Rf build

$(LIB_DIR)/libctriplet.a:
	make -C $(LIB_DIR) libctriplet.a

clean: libclean
	rm -fv *.so
#	rm -fv libctriplet.a

libclean:
	make -C $(LIB_DIR) clean
