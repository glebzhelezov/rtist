UNAME := $(shell uname -s)
ARCH := $(shell uname -m)

ifeq ($(UNAME),Darwin)
  BREW_OMP_PREFIX := $(shell brew --prefix libomp 2>/dev/null || echo "")

  ifeq ($(ARCH),arm64)
    CC = clang
    OPT_FLAGS = -Ofast -mcpu=apple-m1
  else
    CC = clang
    OPT_FLAGS = -Ofast -march=native
  endif

  ifneq ($(BREW_OMP_PREFIX),)
    OPENMP_FLAGS = -Xpreprocessor -fopenmp -I$(BREW_OMP_PREFIX)/include
    OPENMP_LIBS = -L$(BREW_OMP_PREFIX)/lib -lomp
  else
    OPENMP_FLAGS = -Xpreprocessor -fopenmp
    OPENMP_LIBS = -lomp
  endif
else
  CC = gcc
  OPENMP_FLAGS = -fopenmp
  OPENMP_LIBS =
  OPT_FLAGS = -Ofast -march=native
endif

# Check for macOS
UNAME := $(shell uname)
ifeq ($(UNAME), Darwin)
    # macOS-specific OpenMP flags
    ARCH := $(shell uname -m)
    ifeq ($(ARCH), arm64)
        # M1/M2 Mac
        OPT_FLAGS = -Ofast -mcpu=apple-m1
    else
        # Intel Mac
        OPT_FLAGS = -Ofast -march=native
    endif
    
    # Try to use Homebrew OpenMP if available
    BREW_PREFIX := $(shell brew --prefix libomp 2>/dev/null || echo "")
    ifneq ($(BREW_PREFIX),)
        OMP_FLAGS = -Xpreprocessor -fopenmp -I$(BREW_PREFIX)/include
        OMP_LINK_FLAGS = -L$(BREW_PREFIX)/lib -lomp
    else
        # Fallback without OpenMP for macOS
        OMP_FLAGS =
        OMP_LINK_FLAGS =
    endif
else
    # Linux and other platforms
    OPT_FLAGS = -Ofast -march=native
    OMP_FLAGS = -fopenmp
    OMP_LINK_FLAGS = -fopenmp
endif

default: libctriplet.a

libctriplet.a: lookup_table.o weights_omp.o
	ar rcs $@ $^

lookup_table.o: lookup_table.c lookup_table.h
	$(CC) -c $(OPT_FLAGS) $(OMP_FLAGS) $<

weights_omp.o: weights_omp.c weights_omp.h 
	$(CC) -c -fPIC $(OPT_FLAGS) $(OMP_FLAGS) $<

clean:
	rm -fv lookup_table.o weights_omp.o 

cleanall: clean
	rm -fv libctriplet.a
