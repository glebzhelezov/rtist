cmake_minimum_required(VERSION 3.12)
project(ctriplet C)

# Set optimization flags based on architecture
if(APPLE)
    # Check if in GitHub Actions
    if(DEFINED ENV{GITHUB_ACTIONS} AND "$ENV{GITHUB_ACTIONS}" STREQUAL "true")
        # Use safe flags for GitHub Actions builds
        set(OPT_FLAGS "-Ofast")
        message(STATUS "Using safe optimization flags for GitHub Actions")
    elseif(CMAKE_SYSTEM_PROCESSOR STREQUAL "arm64")
        set(OPT_FLAGS "-Ofast -mcpu=apple-m1")
    else()
        set(OPT_FLAGS "-Ofast -march=native")
    endif()
else()
    set(OPT_FLAGS "-Ofast -march=native")
endif()

# Handle OpenMP for macOS
set(OPENMP_FOUND FALSE)
if(APPLE)
    # Try to find Homebrew's OpenMP installation
    find_program(BREW_EXECUTABLE brew)
    if(BREW_EXECUTABLE)
        execute_process(
            COMMAND ${BREW_EXECUTABLE} --prefix libomp
            OUTPUT_VARIABLE BREW_LIBOMP_PREFIX
            ERROR_QUIET
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        
        if(BREW_LIBOMP_PREFIX)
            message(STATUS "Found Homebrew OpenMP: ${BREW_LIBOMP_PREFIX}")
            set(OpenMP_C_FLAGS "-Xpreprocessor -fopenmp -I${BREW_LIBOMP_PREFIX}/include")
            set(OpenMP_C_LIB_NAMES "omp")
            set(OpenMP_omp_LIBRARY "${BREW_LIBOMP_PREFIX}/lib/libomp.dylib")
            set(OPENMP_FOUND TRUE)
            
            # Add these to include and link directories
            include_directories(${BREW_LIBOMP_PREFIX}/include)
            link_directories(${BREW_LIBOMP_PREFIX}/lib)
        else()
            message(WARNING "Homebrew OpenMP not found. Building without OpenMP support.")
        endif()
    else()
        message(WARNING "Homebrew not found. Building without OpenMP support.")
    endif()
else()
    # Standard OpenMP support for non-macOS platforms
    find_package(OpenMP)
endif()

# Set compiler flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OPT_FLAGS}")
if(OPENMP_FOUND)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    message(STATUS "Building with OpenMP support")
else()
    # Define a macro to tell the C code to not use OpenMP features
    add_definitions(-DNO_OMP)
    message(STATUS "Building without OpenMP support")
endif()

# Create static library
add_library(ctriplet STATIC
    lookup_table.c
    weights_omp.c
)

# Include directories
target_include_directories(ctriplet PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# Link with OpenMP
if(OPENMP_FOUND)
    if(APPLE)
        target_link_libraries(ctriplet PUBLIC omp)
    else()
        target_link_libraries(ctriplet PUBLIC OpenMP::OpenMP_C)
    endif()
endif()

# Position independent code
set_property(TARGET ctriplet PROPERTY POSITION_INDEPENDENT_CODE ON)

# Installation
install(TARGETS ctriplet
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)