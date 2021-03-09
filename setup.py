from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

comb2_extension = Extension(
        name='comb2',
        sources=['triplet_omp_py.pyx'],
        libraries=['ctriplet'],
        library_dirs=['lib'],
        include_dirs=['lib'],
        extra_compile_args=['-fopenmp'],
        extra_link_args=['-fopenmp'],
        )

setup(
        name='comb2',
        ext_modules=cythonize([comb2_extension], language_level=3)
        )
