.PHONY: all test clean

all: test
	pip wheel . --no-deps -w wheels/

test:
	python -m pytest beef/test

clean:
	rm -rf dist wheels
