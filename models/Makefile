SHELL=/bin/sh
SUBDIRS=shared morel91 par
MAKE=make

all:
	$(MAKE) -C shared install
	for dir in $(SUBDIRS) ; \
	do \
		$(MAKE) -C $$dir all; \
	done

clean:
	for dir in $(SUBDIRS) ; \
	do \
		$(MAKE) -C $$dir clean; \
	done

rebuild:
	for dir in $(SUBDIRS) ; \
	do \
		$(MAKE) -C $$dir rebuild; \
	done

install:
	for dir in $(SUBDIRS) ; \
	do \
		$(MAKE) -C $$dir install; \
	done
