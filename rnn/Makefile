CC=gcc
CFLAGS=-I. -lm
DEPS = rnn.h
OBJ = c_fifo.o rnn.o 

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

main: $(OBJ)
	$(CC) -o $@ $^ $(CFLAGS)
