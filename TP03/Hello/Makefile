PACKAGE = Hello
MAINFILE = main

ifndef ANTLR4
abort:
	$(error variable ANTLR4 is not set)
endif

all: $(PACKAGE).g4
	$(ANTLR4) $^ -Dlanguage=Python3

run: $(MAINFILE).py
	python3 $^

clean:
	rm -rf *~ $(PACKAGE)*.py $(PACKAGE)*.pyc *.tokens  __pycache* *.interp
