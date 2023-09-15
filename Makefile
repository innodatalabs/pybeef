.PHONY: all clean

all:
	pip wheel .

clean:
	rm -rf *.whl
