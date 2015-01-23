
all: check

check: test.xml
	./test.sh || ./cleanup.sh

#Run check-data target to test against known disk image contents
check-data: check-testdata
	python2.7 dfxmlfs.py -o imgfile=testdata/nps-2009-ntfs1/ntfs1-gen1.E01 -o xmlfile=testdata/nps-2009-ntfs1/ntfs1-gen1.E01.dfxml testdir

check-testdata:
	$(MAKE) -C testdata/nps-2009-ntfs1

debug:
	grep --color DEBUG stderr.log

test.xml: deps/dfxml/samples/difference_test_0.xml
	ln -s $< $@
