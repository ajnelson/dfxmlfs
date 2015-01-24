
all: check

check: test.xml
	./test.sh || ./cleanup.sh

#Run check-data target to test against known disk image contents
check-data: check-testdata

check-testdata: \
  check-testdata-ntfs-gen1 \
  check-testdata-ntfs-gen2

check-testdata-ntfs-gen1:
	$(MAKE) -C testdata/nps-2009-ntfs1/ntfs-gen1 check

check-testdata-ntfs-gen2:
	$(MAKE) -C testdata/nps-2009-ntfs1/ntfs-gen2 check

debug:
	grep --color DEBUG stderr.log

download: download-testdata

download-testdata: \
  download-testdata-ntfs-gen1 \
  download-testdata-ntfs-gen2

download-testdata-ntfs-gen1:
	$(MAKE) -C testdata/nps-2009-ntfs1/ntfs-gen1 download

download-testdata-ntfs-gen2:
	$(MAKE) -C testdata/nps-2009-ntfs1/ntfs-gen2 download

test.xml: deps/dfxml/samples/difference_test_0.xml
	ln -s $< $@
