CC=gcc
CFLAGS=-I. -lm
DEPS = c_fifo.h
OBJ = c_fifo.o 

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

c_fifo: $(OBJ)
	$(CC) -o $@ $^ $(CFLAGS)
