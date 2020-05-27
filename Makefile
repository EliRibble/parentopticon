CFLAGS=$(shell pkg-config --cflags glib-2.0)
LDFLAGS=$(shell pkg-config --libs glib-2.0 libcap)

bin/cn_proc: cn_proc/cn_proc.c
	$(CC) cn_proc/cn_proc.c $(CFLAGS) -o bin/cn_proc $(LDFLAGS) 
	
cn_proc: bin/cn_proc
all: bin/cn_proc
