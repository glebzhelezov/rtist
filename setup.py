#from distutils.core import setup
from setuptools import setup, find_packages
from distutils.extension import Extension
from Cython.Build import cythonize
import cysignals
# setup.py is only called via the Makefile, which updates this...
try:
    from trippy.median_triplet_version import __version__ as version
except:
    import datetime
    version = datetime.datetime.now().timestamp()

compile_time_env = dict(HAVE_CYSIGNALS=False)
# detect `cysignals`
if cysignals is not None:
    compile_time_env["HAVE_CYSIGNALS"] = True

comb2_extension = Extension(
    # name="comb2",
    name="trippy.triplet_omp",
    sources=["src/trippy/triplet_omp_py.pyx"],
    libraries=["ncurses", "ctriplet"],
    library_dirs=["lib"],
    include_dirs=["lib"],
    extra_compile_args=["-Ofast", "-fopenmp", "-march=native"],
    extra_link_args=["-fopenmp"],
)

bitsnbobs = Extension(
    name="trippy.bitsnbobs",
    sources=["src/trippy/bitsnbobs.pyx"],
    extra_compile_args=["-Ofast", "-march=native"],
)

scipy_comb = Extension(
    name="trippy.scipycomb",
    sources=["src/trippy/scipy_comb.pyx"],
    extra_compile_args=["-lm", "-Ofast", "-march=native"],
)

setup(
    name="trippy",
    author="Gleb Zhelezov",
    author_email="gzhelezo@unm.edu",
    description="A package for finding the exact median triplet tree",
    version=version,
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    ext_modules=cythonize(
        [comb2_extension, bitsnbobs, scipy_comb],
        language_level=3,
        compile_time_env=compile_time_env,
    ),
    scripts=['scripts/mediantriplet','scripts/tripthrough'],
)
