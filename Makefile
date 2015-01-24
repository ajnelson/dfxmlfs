
all: check

check: test.xml
	./test.sh || ./cleanup.sh

#Run check-data target to test against known disk image contents
check-data: check-testdata

check-testdata:
	$(MAKE) -C testdata/nps-2009-ntfs1/ntfs-gen1 check

debug:
	grep --color DEBUG stderr.log

download: download-testdata

download-testdata:
	$(MAKE) -C testdata/nps-2009-ntfs1/ntfs-gen1 download

test.xml: deps/dfxml/samples/difference_test_0.xml
	ln -s $< $@
