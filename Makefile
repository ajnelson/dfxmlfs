
all: check

check: test.xml
	./test.sh || ./cleanup.sh

debug:
	grep --color DEBUG stderr.log

test.xml: deps/dfxml/samples/difference_test_0.xml
	ln -s $< $@
