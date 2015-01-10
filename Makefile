
all: check

check:
	./test.sh || ./cleanup.sh
