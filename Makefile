CFLAGS=$(shell pkg-config --cflags glib-2.0)
LDFLAGS=$(shell pkg-config --libs glib-2.0)

bin/cn_proc: obj/cn_proc.o
	$(CC) cn_proc/cn_proc.c $(CFLAGS) -o bin/cn_proc $(LDFLAGS) 
	
cn_proc: bin/cn_proc
all: bin/cn_proc
