CC = gcc
PROGRESS_DIR = progressbar

default: libctriplet.a

libctriplet.a: lookup_table.o weights_omp.o $(PROGRESS_DIR)/statusbar.o $(PROGRESS_DIR)/progressbar.o
	ar rcs $@ $^

lookup_table.o: lookup_table.c lookup_table.h
	$(CC) -c -Ofast -fopenmp -march=native $<

weights_omp.o: weights_omp.c weights_omp.h 
	$(CC) -c -fPIC -I$(PROGRESS_DIR)/include/progressbar -Ofast -fopenmp -march=native $<

$(PROGRESS_DIR)/statusbar.o:
	make -C $(PROGRESS_DIR)

$(PROGRESS_DIR)/progressbar.o:
	make -C $(PROGRESS_DIR)

clean:
	rm -fv lookup_table.o weights_omp.o 
	make -C $(PROGRESS_DIR) clean

cleanall: clean
	rm -fv libctriplet.a
