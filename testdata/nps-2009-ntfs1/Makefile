
all: ntfs1-gen1.E01.dfxml

ntfs1-gen1.E01:
	@echo "Please soft-link the disk image '$@'." >&2
	exit 1

ntfs1-gen1.E01.dfxml: ntfs1-gen1.E01
	rm -f _$@
	fiwalk -X _$@ $^
	mv _$@ $@
