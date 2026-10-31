# Builds the mtrip Python package's compiled modules. Driven by
# scikit-build-core: build with `uv build` or `pip install .`, not by running
# cmake directly. (The C library alone can be built with cmake; see
# lib/CMakeLists.txt.)
cmake_minimum_required(VERSION 3.15...3.31)
project(mtrip LANGUAGES C)

if(NOT SKBUILD)
    message(WARNING "This project is meant to be built through scikit-build-core, e.g. `uv build` or `pip install .`")
endif()

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(Cython MODULE REQUIRED VERSION 3.0)
include(UseCython)

add_subdirectory(lib)

# cysignals ships its .pxd files and C headers inside its Python package.
execute_process(
    COMMAND "${Python_EXECUTABLE}" -c "import cysignals, os; print(os.path.dirname(cysignals.__file__))"
    OUTPUT_VARIABLE CYSIGNALS_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE _cysignals_result
)
if(NOT _cysignals_result EQUAL 0)
    message(FATAL_ERROR "mtrip: cysignals must be importable at build time")
endif()
get_filename_component(CYSIGNALS_PARENT_DIR "${CYSIGNALS_DIR}" DIRECTORY)

# mtrip_cython_module(<module> <pyx file>): build src/mtrip/<pyx> as mtrip.<module>.
function(mtrip_cython_module module pyx)
    cython_transpile("src/mtrip/${pyx}"
        LANGUAGE C
        MODULE_NAME "mtrip.${module}"
        INCLUDE_DIRECTORIES "${CYSIGNALS_PARENT_DIR}"
        OUTPUT_VARIABLE c_source
    )
    python_add_library(${module} MODULE "${c_source}" WITH_SOABI)
    target_link_libraries(${module} PRIVATE mtrip_build_flags)
    install(TARGETS ${module} DESTINATION mtrip)
endfunction()

mtrip_cython_module(bitsnbobs bitsnbobs.pyx)
mtrip_cython_module(scipycomb scipy_comb.pyx)
mtrip_cython_module(triplet_omp triplet_omp_py.pyx)
target_link_libraries(triplet_omp PRIVATE ctriplet)
target_include_directories(triplet_omp PRIVATE "${CYSIGNALS_DIR}")
