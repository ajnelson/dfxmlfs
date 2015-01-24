
#Run 'make download' to fetch, verify, and link the disk image.
#Run 'make check' to test file reading

SHELL = /bin/bash

HASH_NTFS1GEN2=27a9053e35aac74608493e755353cb95

all: ntfs1-gen2.E01.dfxml

#Take care to verify this download.
_ntfs1-gen2.E01:
	rm -f $@
	wget http://digitalcorpora.org/corpora/disk-images/nps-2009-ntfs1/ntfs1-gen2.E01 -O $@

check: ntfs1-gen2.E01.dfxml
	./test.sh

download: _ntfs1-gen2.E01
	ewfverify $^ > $^.ewfverify.out.log
	test $$(grep $(HASH_NTFS1GEN2) $^.ewfverify.out.log | wc -l ) -eq 2 || (echo "ERROR:Expected checksum not found in log.">&2 ; exit 1)
	rm -f ntfs1-gen2.E01 #Remove old link if it exists
	ln -s {_,}ntfs1-gen2.E01
	@echo "Disk image downloaded and verified." >&2

ntfs1-gen2.E01:
	@echo "Please soft-link the disk image '$@'." >&2
	@echo "You can run 'make download' to download, verify, and link this disk image." >&2
	exit 1

ntfs1-gen2.E01.dfxml: ntfs1-gen2.E01
	rm -f _$@
	fiwalk -X _$@ $^
	mv _$@ $@
