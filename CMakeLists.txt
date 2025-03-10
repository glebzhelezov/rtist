cmake_minimum_required(VERSION 3.12)
project(rtist C CXX)

# Set Python version requirements
set(Python_ADDITIONAL_VERSIONS 3.6 3.7 3.8 3.9 3.10 3.11 3.12 3.13)
set(PYBIND11_PYTHON_VERSION 3.6)

# Add C extension subdirectory
add_subdirectory(src/mtrip/_c_ext)

# Installation settings
include(GNUInstallDirs)