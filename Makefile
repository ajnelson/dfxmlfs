
all: check

check:
	./test.sh || ./cleanup.sh

debug:
	grep --color DEBUG stderr.log
