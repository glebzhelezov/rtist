CC = gcc

default: libctriplet.a

libctriplet.a: lookup_table.o scores_omp.o
	ar rcs $@ $^

lookup_table.o: lookup_table.c lookup_table.h
	$(CC) -c -Ofast -mpopcnt -fopenmp $<

scores_omp.o: scores_omp.c scores_omp.h
	$(CC) -c -Ofast -mpopcnt -fopenmp $<

oclean:
	rm -fv lookup_table.o scores_omp.o 

clean: oclean
	rm -fv libctriplet.a
