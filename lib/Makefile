CC = gcc

default: libctriplet.a

libctriplet.a: lookup_table.o scores_omp.o
	ar rcs $@ $^

lookup_table.o: lookup_table.c lookup_table.h
	$(CC) -c $<

scores_omp.o: scores_omp.c scores_omp.h
	$(CC) -c $<

oclean:
	rm *.o

clean:
	rm *.o *.a
