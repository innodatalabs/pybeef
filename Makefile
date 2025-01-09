.PHONY: all test clean

all: test
	pip wheel .

test:
	python -m pytest beef/test

clean:
	rm -rf *.whl dist
