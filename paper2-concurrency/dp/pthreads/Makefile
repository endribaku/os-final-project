# Makefile for the pthreads dining-philosophers variants.
# Linux-only (sem-free here, but the dp_common watchdog assumes /proc-style
# timing semantics that are nicer on Linux). Build inside the VM.

CC       ?= gcc
CFLAGS   ?= -O2 -Wall -Wextra -std=c11 -pthread
LDLIBS   ?= -lm -lpthread

TARGETS   = dphil_2 dphil_4 dphil_5
COMMON    = dp_common.c
COMMON_H  = dp_common.h

.PHONY: all clean smoke

all: $(TARGETS)

dphil_%: dphil_%.c $(COMMON) $(COMMON_H)
	$(CC) $(CFLAGS) -o $@ $< $(COMMON) $(LDLIBS)

# quick correctness check
smoke: $(TARGETS)
	@for t in $(TARGETS); do \
	    echo "--- $$t ---"; \
	    ./$$t --N 5 --duration-sec 1; \
	done

clean:
	rm -f $(TARGETS)
