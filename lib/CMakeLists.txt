# The C core: a static library, buildable on its own with
#   cmake -S lib -B build/lib && cmake --build build/lib
# and used by the top-level build for the mtrip.triplet_omp extension.
cmake_minimum_required(VERSION 3.15...3.31)
project(ctriplet LANGUAGES C)

option(MTRIP_OPENMP "Use OpenMP for the parallel weight computation if available" ON)
option(MTRIP_NATIVE "Tune for the build machine's CPU; the result is not portable" OFF)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# Compile options shared by every mtrip target, C library and Cython modules.
add_library(mtrip_build_flags INTERFACE)
if(MTRIP_NATIVE)
    include(CheckCCompilerFlag)
    check_c_compiler_flag(-march=native MTRIP_HAS_MARCH_NATIVE)
    check_c_compiler_flag(-mcpu=native MTRIP_HAS_MCPU_NATIVE)
    if(MTRIP_HAS_MARCH_NATIVE)
        target_compile_options(mtrip_build_flags INTERFACE -march=native)
    elseif(MTRIP_HAS_MCPU_NATIVE)
        target_compile_options(mtrip_build_flags INTERFACE -mcpu=native)
    else()
        message(WARNING "mtrip: MTRIP_NATIVE=ON, but the compiler accepts neither -march=native nor -mcpu=native")
    endif()
endif()

add_library(ctriplet STATIC weights_omp.c lookup_table.c)
target_include_directories(ctriplet PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(ctriplet PUBLIC mtrip_build_flags)
set_target_properties(ctriplet PROPERTIES
    C_STANDARD 99
    C_STANDARD_REQUIRED ON
    POSITION_INDEPENDENT_CODE ON  # it ends up inside a Python extension module
)

if(MTRIP_OPENMP)
    # Apple clang has no bundled OpenMP runtime; use Homebrew's libomp if present.
    if(APPLE AND NOT DEFINED OpenMP_ROOT AND NOT DEFINED ENV{OpenMP_ROOT})
        find_program(MTRIP_BREW brew)
        if(MTRIP_BREW)
            execute_process(
                COMMAND "${MTRIP_BREW}" --prefix libomp
                OUTPUT_VARIABLE _mtrip_libomp
                OUTPUT_STRIP_TRAILING_WHITESPACE
                ERROR_QUIET
                RESULT_VARIABLE _mtrip_brew_result
            )
            if(_mtrip_brew_result EQUAL 0 AND EXISTS "${_mtrip_libomp}/include/omp.h")
                set(OpenMP_ROOT "${_mtrip_libomp}")
            endif()
        endif()
    endif()

    find_package(OpenMP COMPONENTS C)
    if(OpenMP_C_FOUND)
        target_link_libraries(ctriplet PUBLIC OpenMP::OpenMP_C)
        message(STATUS "mtrip: building with OpenMP ${OpenMP_C_VERSION}")
    else()
        message(WARNING "mtrip: OpenMP not found; building single-threaded")
    endif()
else()
    message(STATUS "mtrip: MTRIP_OPENMP=OFF; building single-threaded")
endif()
