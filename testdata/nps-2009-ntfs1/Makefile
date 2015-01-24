
#Run 'make download' to fetch, verify, and link the disk image.

SHELL = /bin/bash

all: ntfs1-gen1.E01.dfxml

#Take care to verify this download.
_ntfs1-gen1.E01:
	rm -f $@
	wget http://digitalcorpora.org/corpora/disk-images/nps-2009-ntfs1/ntfs1-gen1.E01 -O $@

download: _ntfs1-gen1.E01
	ewfverify $^
	ln -s {_,}ntfs1-gen1.E01

ntfs1-gen1.E01:
	@echo "Please soft-link the disk image '$@'." >&2
	exit 1

ntfs1-gen1.E01.dfxml: ntfs1-gen1.E01
	rm -f _$@
	fiwalk -X _$@ $^
	mv _$@ $@
