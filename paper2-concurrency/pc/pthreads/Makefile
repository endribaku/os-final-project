# Makefile for the pthreads producer-consumer.
# Linux-only (uses sem_init unnamed semaphores). Build inside the VM.

CC      ?= gcc
CFLAGS  ?= -O2 -Wall -Wextra -std=c11 -pthread
LDLIBS  ?= -lm -lpthread

TARGET   = producer_consumer
SRC      = producer_consumer.c

.PHONY: all clean run smoke

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $@ $< $(LDLIBS)

# quick correctness check
smoke: $(TARGET)
	./$(TARGET) --N 8 --M 2 --K 2 --items 1000

clean:
	rm -f $(TARGET)
