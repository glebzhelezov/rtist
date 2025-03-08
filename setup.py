# from distutils.core import setup
from setuptools import setup, find_packages
from distutils.extension import Extension
from Cython.Build import cythonize
import platform
import subprocess
import os
import re

# Get version from __init__.py
def get_version():
    init_path = os.path.join('src', 'mtrip', '__init__.py')
    if os.path.exists(init_path):
        with open(init_path, 'r') as f:
            version_match = re.search(r"__version__\s*=\s*['\"]([^'\"]*)['\"]", f.read())
            if version_match:
                return version_match.group(1)
    # Fallback if version not found
    import datetime
    return datetime.datetime.now().timestamp()

version = get_version()

compile_time_env = dict(HAVE_CYSIGNALS=False)
# check if cysignals is available as an optional dependency
try:
    import cysignals
    compile_time_env['HAVE_CYSIGNALS'] = True
except ImportError:
    pass

# used to configure setup for different configurations
is_macos = platform.system() == "Darwin"
is_arm64 = platform.machine() == "arm64"
brew_prefix = None

# check for Homebrew OpenMP on macOS
if is_macos:
    try:
        brew_prefix = subprocess.check_output(
            ["brew", "--prefix", "libomp"], universal_newlines=True
        ).strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        brew_prefix = None

# configure compile and link arguments based on platform
extra_compile_args = []
extra_link_args = []
library_dirs = ["lib"]
include_dirs = ["lib"]

if is_macos:
    if is_arm64:
        opt_flags = ["-Ofast", "-mcpu=apple-m1"]
    else:
        # Intel macs
        opt_flags = ["-Ofast", "-march=native"]

    if brew_prefix:
        # use Homebrew's OpenMP
        omp_compile_flags = ["-Xpreprocessor", "-fopenmp", f"-I{brew_prefix}/include"]
        omp_link_flags = [f"-L{brew_prefix}/lib", "-lomp"]
        include_dirs.append(f"{brew_prefix}/include")
        library_dirs.append(f"{brew_prefix}/lib")
    else:
        # ...or not, if not available
        print("Not using OpenMP from Homebrew. OpenMP will be disabled.")
        omp_compile_flags = []
        omp_link_flags = []

    extra_compile_args = opt_flags + omp_compile_flags
    extra_link_args = omp_link_flags


comb2_extension = Extension(
    name="mtrip.triplet_omp",
    sources=["src/mtrip/triplet_omp_py.pyx"],
    libraries=["ncurses", "ctriplet"],
    library_dirs=library_dirs,
    include_dirs=include_dirs,
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
)

# architecture-specific flags not related to OpenMP
basic_compile_args = []
if is_macos and is_arm64:
    basic_compile_args = ["-Ofast", "-mcpu=apple-m1"]
elif is_macos:
    basic_compile_args = ["-Ofast", "-march=native"]
else:
    basic_compile_args = ["-Ofast", "-march=native"]

bitsnbobs = Extension(
    name="mtrip.bitsnbobs",
    sources=["src/mtrip/bitsnbobs.pyx"],
    extra_compile_args=extra_compile_args,
)

scipy_comb = Extension(
    name="mtrip.scipycomb",
    sources=["src/mtrip/scipy_comb.pyx"],
    extra_compile_args=["-lm"] + basic_compile_args,
)

setup(
    name="mtrip",
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
    scripts=["scripts/mtrip", "scripts/mtrip-combine", "scripts/mtrip-suboptimal"],
    # dependencies are in pyproject.toml
)
