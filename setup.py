# from distutils.core import setup
from setuptools import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import cysignals

compile_time_env = dict(HAVE_CYSIGNALS=False)
# detect `cysignals`
if cysignals is not None:
    compile_time_env["HAVE_CYSIGNALS"] = True

comb2_extension = Extension(
    name="comb2",
    sources=["triplet_omp_py.pyx"],
    libraries=["ctriplet", "ncurses"],
    library_dirs=["lib"],
    include_dirs=["lib"],
    extra_compile_args=["-Ofast", "-fopenmp", "-march=native"],
    extra_link_args=["-fopenmp"],
)

bitsnbobs = Extension(
    name="bitsnbobs",
    sources=["bitsnbobs.pyx"],
    extra_compile_args=["-Ofast", "-march=native"],
)

scipycomb = Extension(
    name="scipycomb",
    sources=["scipy_comb.pyx"],
    extra_compile_args=["-Ofast", "-march=native"],
)

setup(
    name="comb2",
    ext_modules=cythonize(
        [comb2_extension, bitsnbobs, scipycomb,],
        language_level=3,
        compile_time_env=compile_time_env,
    ),
)
