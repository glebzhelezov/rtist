import os
import platform
import subprocess
import sys
from distutils.extension import Extension
from setuptools.command.build_ext import build_ext

from Cython.Build import cythonize
from setuptools import find_packages, setup

class CMakeBuild(build_ext):
    def run(self):
        # Run CMake to build the C library
        cmake_dir = os.path.abspath(os.path.dirname(__file__))
        build_dir = os.path.join(cmake_dir, 'build')
        
        if not os.path.exists(build_dir):
            os.makedirs(build_dir)
            
        cmake_cmd = ["cmake", ".."]
        
        cmake_cmd.extend(["-DCMAKE_POSITION_INDEPENDENT_CODE=ON"])
        
        try:
            subprocess.check_call(cmake_cmd, cwd=build_dir)
            
            # Determine the build tool (make or ninja)
            if os.path.exists(os.path.join(build_dir, "Makefile")):
                build_cmd = ["make"]
            elif os.path.exists(os.path.join(build_dir, "build.ninja")):
                build_cmd = ["ninja"]
            else:
                print("Warning: No Makefile or build.ninja found, skipping C library build")
                build_cmd = None
                
            # Build with the appropriate tool
            if build_cmd:
                subprocess.check_call(build_cmd, cwd=build_dir)
        except subprocess.CalledProcessError as e:
            print(f"Warning: CMake build failed: {e}")
            print("Continuing with Cython build...")
        
        # Let setuptools handle Cython extensions
        super().run()

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
library_dirs = ["src/mtrip/_c_ext"]
include_dirs = ["src/mtrip/_c_ext"]

# Check if we're building a universal binary
universal_build = False
if os.environ.get("ARCHFLAGS", "").find("universal2") >= 0:
    universal_build = True
    print("Detected universal2 build, avoiding architecture-specific flags")

if is_macos:
    if universal_build:
        # Safe flags for universal builds (arm64 + x86_64)
        opt_flags = ["-Ofast"]
    elif is_arm64:
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
else:
    if universal_build:
        extra_compile_args = ["-Ofast", "-fopenmp"]
    else:
        extra_compile_args = ["-Ofast", "-march=native", "-fopenmp"]
    extra_link_args = ["-fopenmp"]


comb2_extension = Extension(
    name="mtrip.triplet_omp",
    sources=["src/mtrip/triplet_omp_py.pyx"],
    libraries=["ctriplet"],
    library_dirs=library_dirs,
    include_dirs=include_dirs,
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
)

# architecture-specific flags not related to OpenMP
basic_compile_args = []
if is_macos:
    if universal_build:
        basic_compile_args = ["-Ofast"]
    elif is_arm64:
        basic_compile_args = ["-Ofast", "-mcpu=apple-m1"]
    else:
        basic_compile_args = ["-Ofast", "-march=native"]
else:
    if universal_build:
        basic_compile_args = ["-Ofast"]
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

extensions = [comb2_extension, bitsnbobs, scipy_comb]

setup(
    name="mtrip",
    author="Gleb Zhelezov",
    author_email="gleb@glebzh.com",
    description="A package for finding the exact median triplet tree (in the context of phylogenetics)",
    version="0.3.0beta",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    ext_modules=cythonize(
        extensions,
        language_level=3,
        compiler_directives={
            "embedsignature": True,
            "binding": True,
        },
    ),
    cmdclass={"build_ext": CMakeBuild},
    python_requires=">=3.6",
    install_requires=[
        "Cython>=3.0.0",
        "cysignals",  # Required for proper signal handling in C extensions
    ],
    extras_require={
        "dev": ["pytest>=6.0", "black", "mypy"],
    },
    entry_points={
        "console_scripts": [
            "mtrip=mtrip.cli.mtrip_cmd:main",
            "mtrip-combine=mtrip.cli.mtrip_combine_cmd:main",
            "mtrip-suboptimal=mtrip.cli.mtrip_suboptimal_cmd:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    test_suite="tests",
    zip_safe=False,
    include_package_data=True,
    package_data={"": ["test_data/*.nwk"]},
)
