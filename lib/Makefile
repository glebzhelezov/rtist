CC = gcc

default: libctriplet.a

libctriplet.a: lookup_table.o weights_omp.o
	ar rcs $@ $^

lookup_table.o: lookup_table.c lookup_table.h
	$(CC) -c -Ofast -fopenmp -march=native $<

weights_omp.o: weights_omp.c weights_omp.h
	$(CC) -c -Ofast -fopenmp -march=native $<

clean:
	rm -fv lookup_table.o weights_omp.o 

cleanall: clean
	rm -fv libctriplet.a
