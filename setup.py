#from distutils.core import setup
from setuptools import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import Cython.Compiler.Options
Cython.Compiler.Options.annotate = True


comb2_extension = Extension(
        name="comb2",
        sources=["triplet_omp_py.pyx"],
        libraries=["ctriplet"],
        library_dirs=["lib"],
        include_dirs=["lib"],
        extra_compile_args=["-Ofast", "-fopenmp", "-march=native", "-ffast-math"],
        extra_link_args=["-fopenmp"],
) 

bitsnbobs = Extension(
        name="bitsnbobs",
        sources=["bitsnbobs.pyx"],
        extra_compile_args=["-Ofast", "-march=native", "-ffast-math"],
        )

scipycomb = Extension(
        name="scipycomb",
        sources=["scipy_comb.pyx"],
        extra_compile_args=["-Ofast", "-march=native", "-ffast-math"],
        )

setup(name="comb2", ext_modules=cythonize([comb2_extension, bitsnbobs, scipycomb], language_level=3, annotate=True))
